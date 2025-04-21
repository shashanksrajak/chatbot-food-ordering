// DOM elements
const menuContainer = document.getElementById('menu-container');
const cartBtn = document.getElementById('cart-btn');
const cartModal = document.getElementById('cart-modal');
const closeCart = document.querySelector('.close-cart');
const cartItems = document.getElementById('cart-items');
const totalPriceElement = document.getElementById('total-price');
const emptyCartMessage = document.querySelector('.empty-cart');

// Global variables
let menuItems = [];
let cart = [];
let currentCategory = 'all';

// Fetch menu items from API
async function fetchMenuItems() {
    try {
        // Get the API endpoint from environment variables or fallback to a default
        const apiEndpoint = process.env.API_ENDPOINT;
        console.log(apiEndpoint)

        const response = await fetch(apiEndpoint);

        console.log(response)

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();

        // Check if the response has the expected structure
        if (data && data.food_items && Array.isArray(data.food_items)) {
            menuItems = data.food_items.map(item => ({
                id: item.id,
                name: item.name,
                description: item.description,
                price: item.price,
                image: `images/${item.image}`,
                category: getCategoryFromDescription(item.description)
            }));

            displayMenuItems();
        } else {
            throw new Error('Invalid data format received from API');
        }
    } catch (error) {
        console.error('Error fetching menu items:', error);
        // Fallback to hardcoded menu if API fails
        useFallbackMenu();
        displayMenuItems();
    }
}

// Function to determine category based on description (as a fallback)
function getCategoryFromDescription(description) {
    const lowerDesc = description.toLowerCase();

    if (lowerDesc.includes('starter') || lowerDesc.includes('appetizer') || lowerDesc.includes('snack')) {
        return 'starters';
    } else if (lowerDesc.includes('bread') || lowerDesc.includes('naan') || lowerDesc.includes('roti')) {
        return 'breads';
    } else if (lowerDesc.includes('dessert') || lowerDesc.includes('sweet')) {
        return 'desserts';
    } else if (lowerDesc.includes('drink') || lowerDesc.includes('beverage') || lowerDesc.includes('lassi')) {
        return 'beverages';
    } else {
        return 'main-course'; // Default category
    }
}

// Fallback menu in case API fails
function useFallbackMenu() {
    console.log('Using fallback menu data');
    menuItems = [

        {
            id: 2,
            name: "Paneer Tikka",
            description: "Marinated cottage cheese cubes grilled to perfection with bell peppers and onions.",
            price: 249,
            image: "images/paneer-tikka.jpg",
            category: "starters"
        },
        {
            id: 3,
            name: "Vegetable Biryani",
            description: "Fragrant basmati rice cooked with mixed vegetables and aromatic spices.",
            price: 199,
            image: "images/veg-biryani.jpg",
            category: "main-course"
        },
        {
            id: 4,
            name: "Naan",
            description: "Soft and fluffy traditional Indian bread baked in a tandoor.",
            price: 49,
            image: "images/naan.jpg",
            category: "breads"
        },
        {
            id: 5,
            name: "Gulab Jamun",
            description: "Deep-fried milk solids soaked in sugar syrup, served warm.",
            price: 99,
            image: "images/gulab-jamun.jpg",
            category: "desserts"
        },
        {
            id: 6,
            name: "Masala Chai",
            description: "Traditional Indian spiced tea with milk and a blend of aromatic spices.",
            price: 59,
            image: "images/masala-chai.jpg",
            category: "beverages"
        },
        {
            id: 7,
            name: "Chicken Biryani",
            description: "Aromatic basmati rice layered with tender chicken and fragrant spices.",
            price: 249,
            image: "images/chicken-biryani.jpg",
            category: "main-course"
        },
        {
            id: 8,
            name: "Samosa",
            description: "Crispy pastry filled with spiced potatoes and peas, deep-fried to golden perfection.",
            price: 79,
            image: "images/samosa.jpg",
            category: "starters"
        },
        {
            id: 9,
            name: "Palak Paneer",
            description: "Cottage cheese cubes in a creamy spinach gravy flavored with aromatic spices.",
            price: 219,
            image: "images/palak-paneer.jpg",
            category: "main-course"
        },
        {
            id: 10,
            name: "Garlic Naan",
            description: "Soft Indian bread topped with garlic and butter, baked in a tandoor.",
            price: 69,
            image: "images/garlic-naan.jpg",
            category: "breads"
        },
        {
            id: 11,
            name: "Rasgulla",
            description: "Soft and spongy cottage cheese balls soaked in sugar syrup.",
            price: 89,
            image: "images/rasgulla.jpg",
            category: "desserts"
        },
        {
            id: 12,
            name: "Mango Lassi",
            description: "Refreshing yogurt-based drink made with ripe mangoes and a hint of cardamom.",
            price: 79,
            image: "images/mango-lassi.jpg",
            category: "beverages"
        }
    ];
}

// Display menu items
function displayMenuItems(category = 'all') {
    menuContainer.innerHTML = '';

    const filteredItems = category === 'all'
        ? menuItems
        : menuItems.filter(item => item.category === category);

    if (filteredItems.length === 0) {
        menuContainer.innerHTML = '<p class="no-items">No items available in this category.</p>';
        return;
    }

    filteredItems.forEach(item => {
        const menuItemElement = document.createElement('div');
        menuItemElement.className = 'menu-item';

        menuItemElement.innerHTML = `
            <img src="${item.image}" alt="${item.name}">
            <div class="menu-item-info">
                <h3 class="menu-item-title">${item.name}</h3>
                <p class="menu-item-desc">${item.description}</p>
                <div class="menu-item-bottom">
                    <span class="menu-item-price">₹${item.price}</span>
                    <button class="add-to-cart" data-id="${item.id}">Add to Cart</button>
                </div>
            </div>
        `;

        menuContainer.appendChild(menuItemElement);
    });

    // Add event listeners to newly created "Add to Cart" buttons
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', function () {
            const id = parseInt(this.getAttribute('data-id'));
            addToCart(id);
        });
    });
}

// Filter menu by category
function filterMenu() {
    const categoryButtons = document.querySelectorAll('.category-btn');
    if (categoryButtons) {
        categoryButtons.forEach(button => {
            button.addEventListener('click', function () {
                const category = this.getAttribute('data-category');

                // Update active button
                categoryButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');

                currentCategory = category;
                displayMenuItems(category);
            });
        });
    }
}

// Add item to cart
function addToCart(id) {
    const item = menuItems.find(item => item.id === id);

    if (!item) return;

    const existingItem = cart.find(cartItem => cartItem.id === id);

    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            ...item,
            quantity: 1
        });
    }

    updateCartUI();

    // Show animation feedback
    const addButton = document.querySelector(`.add-to-cart[data-id="${id}"]`);
    addButton.textContent = 'Added!';
    addButton.style.backgroundColor = '#4CAF50';

    setTimeout(() => {
        addButton.textContent = 'Add to Cart';
        addButton.style.backgroundColor = '';
    }, 1000);
}

// Update cart UI
function updateCartUI() {
    if (cart.length === 0) {
        emptyCartMessage.style.display = 'block';
        cartItems.innerHTML = '';
        cartItems.appendChild(emptyCartMessage);
    } else {
        emptyCartMessage.style.display = 'none';
        renderCartItems();
    }

    // Update cart button count
    const cartCount = cart.reduce((total, item) => total + item.quantity, 0);
    cartBtn.innerHTML = `<i class="fas fa-shopping-cart"></i> Cart (${cartCount})`;

    // Update total price
    const totalPrice = cart.reduce((total, item) => total + (item.price * item.quantity), 0);
    totalPriceElement.textContent = totalPrice;
}

// Render cart items
function renderCartItems() {
    cartItems.innerHTML = '';

    cart.forEach(item => {
        const cartItemElement = document.createElement('div');
        cartItemElement.className = 'cart-item';

        cartItemElement.innerHTML = `
            <img src="${item.image}" alt="${item.name}">
            <div class="cart-item-info">
                <h4 class="cart-item-title">${item.name}</h4>
                <p class="cart-item-price">₹${item.price}</p>
                <div class="cart-item-actions">
                    <button class="decrease-quantity" data-id="${item.id}">-</button>
                    <span class="cart-item-quantity">${item.quantity}</span>
                    <button class="increase-quantity" data-id="${item.id}">+</button>
                    <button class="remove-item" data-id="${item.id}">🗑️</button>
                </div>
            </div>
        `;

        cartItems.appendChild(cartItemElement);
    });

    // Add event listeners for cart item actions
    document.querySelectorAll('.decrease-quantity').forEach(button => {
        button.addEventListener('click', function () {
            const id = parseInt(this.getAttribute('data-id'));
            decreaseQuantity(id);
        });
    });

    document.querySelectorAll('.increase-quantity').forEach(button => {
        button.addEventListener('click', function () {
            const id = parseInt(this.getAttribute('data-id'));
            increaseQuantity(id);
        });
    });

    document.querySelectorAll('.remove-item').forEach(button => {
        button.addEventListener('click', function () {
            const id = parseInt(this.getAttribute('data-id'));
            removeFromCart(id);
        });
    });
}

// Increase item quantity
function increaseQuantity(id) {
    const item = cart.find(item => item.id === id);
    if (item) {
        item.quantity += 1;
        updateCartUI();
    }
}

// Decrease item quantity
function decreaseQuantity(id) {
    const item = cart.find(item => item.id === id);
    if (item) {
        item.quantity -= 1;

        if (item.quantity <= 0) {
            removeFromCart(id);
        } else {
            updateCartUI();
        }
    }
}

// Remove item from cart
function removeFromCart(id) {
    cart = cart.filter(item => item.id !== id);
    updateCartUI();
}

// Toggle cart modal
function toggleCart() {
    cartModal.style.display = cartModal.style.display === 'block' ? 'none' : 'block';

    // Close cart when clicking outside
    if (cartModal.style.display === 'block') {
        document.body.style.overflow = 'hidden'; // Prevent scrolling
    } else {
        document.body.style.overflow = '';
    }
}

// Event Listeners
window.addEventListener('DOMContentLoaded', () => {
    // Fetch menu items first
    fetchMenuItems();

    // Setup other event listeners
    filterMenu();

    cartBtn.addEventListener('click', toggleCart);
    closeCart.addEventListener('click', toggleCart);

    cartModal.addEventListener('click', function (e) {
        if (e.target === this) {
            toggleCart();
        }
    });

    // Checkout button
    document.querySelector('.checkout-btn').addEventListener('click', function () {
        if (cart.length === 0) {
            alert('Your cart is empty! Add some items before checking out.');
        } else {
            alert('Thank you for your order! Your delicious food will be on its way soon.');
            cart = [];
            updateCartUI();
            toggleCart();
        }
    });
});