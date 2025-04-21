# import modules
from datetime import date
from typing import Annotated
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
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

        if session_id in in_progress_orders:
            current_order: dict = in_progress_orders[session_id]
            current_order.update(new_food_dict)
        else:
            in_progress_orders[session_id] = new_food_dict

        print(in_progress_orders)

        # TODO: add a string response with food items and qty
        return JSONResponse(content={
            "fulfillmentText": f"Added items. Anything else? If you are done you can say done and I will place your order."

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
            "fulfillmentText": f"Your order status is {order.status}"
        })
    except Exception as e:
        print(e)
        return JSONResponse(content={
            "fulfillmentText": f"Invalid Order ID. Please provide correct Order ID."
        })


def remove_order():
    pass


def complete_order(session_id: str):
    if session_id not in in_progress_orders:
        fulfillmentText = "I am having trouble finding your order. Sorry for this inconvenience. Please add your order again by saying New Order"
    else:
        order = in_progress_orders[session_id]

        # Generate a random 6-digit order ID
        order_id = random.randint(100000, 999999)
        print("order_id", order_id)
        print("order", order)

        with Session(engine) as session:
            for food_item, quantity in order.items():
                food_item_record = session.exec(
                    select(FoodItem).where(FoodItem.name.ilike(f"%{food_item}%"))).first()
            if not food_item_record:
                fulfillmentText = f"Sorry, we don't have {food_item} in our menu."
                return JSONResponse(content={"fulfillmentText": fulfillmentText})

            new_order = Order(
                order_id=order_id,
                food_item_id=food_item_record.id,
                status="Preparing",
                quantity=quantity,
                total_price=food_item_record.price * quantity,
                created_at=date.today()
            )
            session.add(new_order)
            del in_progress_orders[session_id]

            session.commit()
            fulfillmentText = f"Your order has been placed successfully. Thank you! Here is your Order ID # {order_id}"

    return JSONResponse(content={
        "fulfillmentText": fulfillmentText
    })


def main():
    print("Hello from backend!")
    uvicorn.run(app, host="::", port=7001)


if __name__ == "__main__":
    main()
