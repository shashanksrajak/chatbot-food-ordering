# import modules
from datetime import date
from typing import Annotated
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlmodel import Field, Session, SQLModel, create_engine, select
import helpers
import random
import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL")


class FoodItem(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    description: str
    image: str
    price: float


class Order(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    order_id: str
    food_item_id: int = Field(foreign_key="fooditem.id")
    status: str
    quantity: int
    total_price: float
    created_at: date


in_progress_orders = {}


engine = create_engine(db_url)

SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


# fastAPI app initalization
app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Hello from Shenky's Food Chatbot Backend."}


@app.get("/food-items")
async def root(session: SessionDep):
    food_items = session.exec(select(FoodItem)).all()
    return {"food_items": food_items}


@app.post("/webhooks/dialogflow")
async def handle_request(request: Request, session: SessionDep):
    # get the json data from incoming request
    payload = await request.json()

    # extract the required info from the body payload
    # check the json response of Dialog Flow
    intent = payload["queryResult"]["intent"]["displayName"]
    parameters = payload["queryResult"]["parameters"]
    output_contexts = payload["queryResult"]["outputContexts"]

    # session id of the chat provided by DialogFlow
    session_id = helpers.extract_session_id(output_contexts[0])
    print(f"sessionid {session_id}")
    print(in_progress_orders)

    match intent:
        case "track.order_context: ongoing-tracking":
            print("Tracking order...")
            return track_order(parameters, session)
        case "order.add_context: ongoing_order":
            print("Adding orders...")
            return add_order(parameters, session_id, session)
        case "order_complete_context: ongoing_order":
            print("Completing the order...")
            return complete_order(session_id)
        case "order.remove_context: ongoing_order":
            print("Removing an item")
            return remove_order(parameters, session_id)
        case "cart.show_context: ongoing-tracking":
            print("Showing cart...")
            return show_cart(session_id)

        case _:
            return JSONResponse(content={
                "fulfillmentText": f"oops! I didn't understand it. Please say New Order or Track Order."
            })


def add_order(parameters: dict, session_id: str, session: SessionDep):
    food_items = parameters["food_item"]
    quantities = parameters["number"]

    # validate data
    if len(food_items) != len(quantities):
        return JSONResponse(content={
            "fulfillmentText": f"oops! Please provide correct quantities with each food item. e.g. (1 mango lassi and 2 chole bhature)"

        })
    else:
        # check if each food item added is a valid item or not
        for item in food_items:
            db_item = session.exec(
                select(FoodItem).where(FoodItem.name.ilike(f"%{item}%"))).first()

            print(db_item)

            if not db_item:
                return JSONResponse(content={
                    "fulfillmentText": f"{item} is not available in our menu. Please add a valid item."

                })

        # add orders in cache
        new_food_dict = dict(zip(food_items, quantities))

        # update existing order
        if session_id in in_progress_orders:
            current_order: dict = in_progress_orders[session_id]
            # current_order.update(new_food_dict)
            for food_item, food_quantity in new_food_dict.items():
                if food_item in current_order:
                    current_order[food_item] += food_quantity
                else:
                    current_order[food_item] = food_quantity

        # create new order
        else:
            in_progress_orders[session_id] = new_food_dict

        print(in_progress_orders)

        items_added = [f"{item} (x{int(qty)})" for item,
                       qty in in_progress_orders[session_id].items()]

        # TODO: add a string response with food items and qty
        return JSONResponse(content={
            "fulfillmentText": f"Added items. Anything else? If you are done you can say done and I will place your order. So far you have added - {", ".join(items_added)}."

        })


def remove_order(parameters: dict, session_id: str):
    food_items = parameters["food_item"]

    not_existing_items = []
    removed_items = []
    # update existing order
    if session_id in in_progress_orders:
        current_order: dict = in_progress_orders[session_id]
        # current_order.update(new_food_dict)
        for food_item in food_items:
            if food_item in current_order:
                del current_order[food_item]
                removed_items.append(food_item)
            else:
                not_existing_items.append(food_item)
        if not current_order:
            del in_progress_orders[session_id]

    else:
        return JSONResponse(content={
            "fulfillmentText": f"oops! Seems like your order does not exist. Please say New Order to start placing a new order."

        })

    print(in_progress_orders)

    removed_text = f"I have removed {', '.join(removed_items)}" if removed_items else "Nothing was removed"
    not_found_text = f"I could not find {', '.join(not_existing_items)}" if not_existing_items else ""

    fulfillment_text = f"{removed_text}. {not_found_text}. Do you want to add anything else? If you are done you can say done and I will place your order."
    # Clean up the fulfillment text
    fulfillment_text = fulfillment_text.replace(". .", ".").strip()
    if fulfillment_text.startswith("I have removed Nothing was removed. "):
        fulfillment_text = fulfillment_text[len(
            "I have removed Nothing was removed. "):].lstrip(". ")

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


def show_cart(session_id):
    """
    Returns back the cart items
    """
    if session_id in in_progress_orders:
        items_added = [f"{item} (x{int(qty)})" for item,
                       qty in in_progress_orders[session_id].items()]
        fulfillment_text = f"You have added these items in your cart: {", ".join(items_added)}"
        return JSONResponse(content={
            "fulfillmentText": fulfillment_text
        })
    else:
        return JSONResponse(content={
            "fulfillmentText": "oops! Your cart looks empty. Please add items by saying New Order."
        })


def track_order(parameters: dict, session: SessionDep):
    """
    Tracks an order by order_id and returns back the status
    """
    try:
        order_id = parameters["order_id"]
        print(order_id)
        order = session.exec(select(Order).where(
            Order.order_id == order_id)).first()
        print(order)
        if not order:
            return JSONResponse(content={
                "fulfillmentText": f"Sorry this Order Id is invalid. Please provide correct Order Id (e.g. 234567)"
            })
        return JSONResponse(content={
            "fulfillmentText": f"Your order is {order.status}. Please keep patience, our chefs are preparing delicious food for you. Thanks for availing our services."
        })
    except Exception as e:
        print(e)
        return JSONResponse(content={
            "fulfillmentText": f"Invalid Order ID. Please provide correct Order ID."
        })


def complete_order(session_id: str):
    if session_id not in in_progress_orders:
        fulfillmentText = "I am having trouble finding your order. Sorry for this inconvenience. Please add your order again by saying New Order"
    else:
        order = in_progress_orders[session_id]

        # Generate a random 6-digit order ID
        order_id = random.randint(100000, 999999)
        print("order_id", order_id)
        print("order", order)

        ordered_item_details = []
        total_bill = 0

        with Session(engine) as session:
            for food_item, quantity in order.items():
                food_item_record = session.exec(
                    select(FoodItem).where(FoodItem.name.ilike(f"%{food_item}%"))).first()
                if not food_item_record:
                    fulfillmentText = f"Sorry, we don't have {food_item} in our menu."
                    return JSONResponse(content={"fulfillmentText": fulfillmentText})
                else:
                    price = food_item_record.price
                    total_price = price * quantity
                    total_bill += total_price

                    new_order = Order(
                        order_id=order_id,
                        food_item_id=food_item_record.id,
                        status="Preparing in Kitchen",
                        quantity=quantity,
                        total_price=total_price,
                        created_at=date.today()
                    )
                    session.add(new_order)
                    ordered_item_details.append(
                        f"{food_item} (x{int(quantity)})")

            del in_progress_orders[session_id]

            session.commit()

            fulfillmentText = f"Your order has been placed successfully. Thank you! Here is your Order ID # {order_id}. Your total bill amount is ₹{total_bill:.2f} and you have ordered: {', '.join(ordered_item_details)}."

    return JSONResponse(content={
        "fulfillmentText": fulfillmentText
    })


def main():
    print("Hello from backend!")
    uvicorn.run(app, host="0.0.0.0", port=9001)
    # uvicorn.run(app, host="::", port=9001)


if __name__ == "__main__":
    main()
