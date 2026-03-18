from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import random
import os

# Initialize driver with None (to be changed later)
driver = None
wait = None
website_main = "https://it.ermenrich.com/"

def create_optimized_driver():
    # Create a Chrome driver optimized for speed
    options = Options()
    options.page_load_strategy = 'eager'
    
    # Block all images, background networking and extensions
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-extensions')
    
    driver = webdriver.Chrome(options=options)
    
    # LONGER timeout for initial load
    driver.set_page_load_timeout(60)
    
    return driver

# Choose random sku
def choose_sku():
    skus = [83836, 83820, 84547, 84545, 83089, 84558, 84638, 84087, 83842, 85574] #first 5 are under 70 EU, last 5 are 70+
    sku_num = random.randint(0,9)
    sku = skus[sku_num]
    return(sku)

def choose_address():
    # Define a list of shipping addresses
    shipping_addresses = [
    {
        'country': 'Italia',
        'city': 'Torino',
        'address': 'Via Alessandro Volta, 2/F',
        'postal_code': '10121'
    },
    {
        'country': 'Italia',
        'city': 'Napoli', 
        'address': 'Via Nuova, 184',
        'postal_code': '80040'
    },
    {
        'country': 'Italia',
        'city': 'Palermo',
        'address': 'Via Gaspare Palermo, 1',
        'postal_code': '90127'
    }
]
    address = shipping_addresses[random.randint(0,2)] 
    return(address) #returns a dictionary


def take_screenshot(name):
    # Helper function to take screenshots for debugging
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    filename = f"screenshots/{name}_{int(time.time())}.png"
    driver.save_screenshot(filename)
    print(f"Screenshot saved as: {filename}")
    return filename

def extract_price(price_text):
    # Extract numeric price from text
    # Remove currency symbols, spaces, and other non-numeric characters except decimal point
    clean_text = re.sub(r'[^\d,]', '', price_text)
    # Replace comma with dot if needed (for European format)
    clean_text = clean_text.replace(',', '.')
    try:
        return float(clean_text)
    except ValueError:
        return None

def get_total_price():
    # Extract the total price in the Basket
    try:
        price_text = driver.find_element(By.CLASS_NAME, 'cart-panel__result-price').text
        price = extract_price(price_text)
        if price is not None:
            return price               
             
        print("Could not find total price on page")
        return None
        
    except Exception as e:
        print(f"Error extracting price: {str(e)}")
        return None

def close_cookie_popup():
    # Close the cookie consent popup if present
    try:
        accept_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".cky-btn.cky-btn-accept"))
                )
        accept_button.click()
        print("Cookie popup closed")
        time.sleep(1)
        return True    
     
    except Exception as e:
        print(f"Error handling cookie popup: {str(e)}")
        return False

def search_for_sku(sku):
    # Search for a specific SKU 
    try:
        print("Navigating to main page...")
        driver.get(website_main)
        time.sleep(1)
        
        close_cookie_popup()
        
        print("Opening search box...")
        search_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".header__search")))
        search_box.click()
        time.sleep(1)
        
        print("Entering SKU...")
        search_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[placeholder*="erca"]')))
        search_input.clear()
        search_input.send_keys(str(sku))
                
        print("Submitting search...")
        search_input.send_keys(Keys.ENTER)
        
        print("Waiting for results to load...")
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".product-card"))
            )
        except:
            time.sleep(2)
        
        print("Search completed successfully")
        return True
        
    except Exception as e:
        print(f"Search failed: {str(e)}")
        take_screenshot("search_error")
        return False

def get_offer_id_for_sku(sku):
    # Extract the offerId for the product with the given SKU
    try:
        print("Finding product offer ID...")
        
        # Find the product card that contains our SKU
        sku_element = wait.until(
            EC.visibility_of_element_located((By.XPATH, f"//*[contains(text(), 'SKU {sku}')]"))
            )
        print(f"Found SKU element: {sku_element.text}")
        
        # Find the product card container
        product_card = sku_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'product-card')]")
        
        # Extract the offer ID from the data attributes
        offer_id = product_card.get_attribute('data-offer-id')
        if offer_id:
            print(f"Found offer ID {offer_id}")
            return int(offer_id)      
        
    except Exception as e:
        print(f"Failed to get offer ID: {str(e)}")
        take_screenshot("offer_id_error")
        return None

def add_to_cart_via_api(offer_id, quantity=1):
    # Add item to cart using the direct API call
    try:
        print("Adding item to cart via API...")
        
        # Execute JavaScript to make the API call
        script = f"""
            // Make the API call to add to cart
            fetch('/rest/methods/user/basket/change', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }},
                body: JSON.stringify({{offerId: {offer_id}, quantity: {quantity}}})
            }})
            .then(response => response.json())
            .then(data => {{
                console.log('API response:', data);
                // Update the UI to reflect the cart change
                if (data.result && data.result.basket) {{
                    // Update add to cart button to show counter
                    const addButtons = document.querySelectorAll('.product-card__basket');
                    addButtons.forEach(button => {{
                        if (button.closest('[data-offer-id="{offer_id}"]') || 
                            button.closest('[data-product-id="{offer_id}"]')) {{
                            button.innerHTML = '<div class="counter"><button type="button" class="counter-btn counter-minus">-</button><input type="number" value="{quantity}" min="1" max="999"><button type="button" class="counter-btn counter-plus">+</button></div>';
                        }}
                    }});
                }}
            }})
            .catch(error => {{
                console.error('API error:', error);
            }});
        """
        
        # Execute the JavaScript
        driver.execute_script(script)
        
        # Wait for the UI to update
        time.sleep(1)
        print("API call completed successfully")
        return True
        
    except Exception as e:
        print(f"Failed to add to cart via API: {str(e)}")
        take_screenshot("api_add_error")
        return False

def navigate_to_cart_directly():
    # Navigate to the cart page directly by URL
    try:
        cart_url = "https://it.ermenrich.com/basket/"
        print(f"Navigating to cart URL: {cart_url}")
        
        driver.get(cart_url)
        time.sleep(1)
        
        # Check if we're on a cart page
        current_url = driver.current_url.lower()
        if "basket" in current_url:
            print("Successfully navigated to basket page")
            return True
        else:
            print(f"Not on basket page. Current URL: {driver.current_url}")
            return False
        
    except Exception as e:
        print(f"Failed to navigate to cart: {str(e)}")
        take_screenshot("cart_navigation_error")
        return False

def check_cart_contents(sku):
    # Check if the cart has our item
    print("Checking cart contents...")
    try:
        sku_element = driver.find_element(By.XPATH, f"//*[contains(text(), 'SKU: {sku}')]")
        take_screenshot("cart_with_our_item")
        return True
            
    except Exception as e:
        print(f"Error checking cart contents: {str(e)}")
        take_screenshot("cart_check_error")
        return False

def select_delivery_option():
    try:
        print("Selecting delivery option...")

        # Define delivery options with their corresponding IDs (equal probability)
        delivery_options = {
            "Consegna standard (standard)": "ID_SHIPPING_METHOD_ID_11",
            "Consegna espressa (express)": "ID_SHIPPING_METHOD_ID_101", # "TBD"
        }

        # Randomly select any delivery option
        selected_option_name = random.choice(list(delivery_options.keys()))
        selected_option_id = delivery_options[selected_option_name]

        print(f"Selected delivery option: {selected_option_name} (ID: {selected_option_id})")

        # Only interact with the UI if it's not the default option
        if selected_option_name != "Consegna standard (standard courier)":
            
            # Find and click the payment option using its ID
            try:
                # Find and click the label of the payment option
                delivery_label = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f"label[for='{selected_option_id}']"))
                )
                print("Found delivery label, attempting to click...")

                # Scroll to the label
                driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", delivery_label)
                time.sleep(0.5)

                # Click the label
                delivery_label.click()
                time.sleep(1)

                # Verify the option was selected by checking the input
                delivery_input = driver.find_element(By.ID, selected_option_id)
                if delivery_input.is_selected():
                    clean_option_name = selected_option_name.lower().replace(' ', '_').replace('\\', '_')
                    take_screenshot(f"selected_{clean_option_name}")
                    print(f"Successfully selected {selected_option_name} delivery option")
                    return True, selected_option_name

                else:
                    print("Label click didn't change selection state")
                    # Fallback to JavaScript click if needed
                    driver.execute_script("arguments[0].click();", delivery_input)
                    time.sleep(1)
                    if delivery_input.is_selected():
                        print("Successfully selected using JavaScript fallback")
                        return True, selected_option_name
                    return False, selected_option_name

            except Exception as e:
                    print(f"Failed to select delivery option {selected_option_name}: {str(e)}")
                    return False, selected_option_name
        else:
                print("Using default delivery option (Standard courier), no action needed")
                return True, selected_option_name

    except Exception as e:
            print(f"Error in delivery selection process: {str(e)}")
            take_screenshot("delivery_option_error")
            return False, "Error"

def select_payment_option(delivery_option):
    # Randomly select a payment option 
    try:
        print("Selecting payment option...")
        
        # Define payment options with their corresponding IDs (equal probability)
        payment_options = {
            "Bonifico bancario (bank transfer)": "ID_PAY_SYSTEM_ID_19",
            "In contanti alla consegna (cash on delivery)": "ID_PAY_SYSTEM_ID_17", # Add 3EU to the total
            "Carta di credito/debito": "ID_PAY_SYSTEM_ID_46",
            "PayPal": "ID_PAY_SYSTEM_ID_18"
        }

        if delivery_option == "Consegna standard (standard)":
            selected_option_name = random.choice(list(payment_options.keys()))
            selected_option_id = payment_options[selected_option_name]
        elif delivery_option == "Consegna espressa (express)":
            # Select out of 2 first options only
            pay_id = random.randint(18,19)
            # First get the value
            selected_option_id = "ID_PAY_SYSTEM_ID_" + str(pay_id)
            # Then get the key from it
            selected_option_name = [key for key, val in payment_options.items() if val == selected_option_id]
        else:
            selected_option_name, selected_option_id = False, False
            print("✗ Unexpected delivery option, can't select payment option")
        
        print(f"Selected payment option: {selected_option_name} (ID: {selected_option_id})")

        # Only interact with the UI if it's not the default option
        if selected_option_name != "Bonifico bancario (bank transfer)":
            # Find and click the payment option using its ID
            try:
                # Find and click the label of the payment option
                payment_label = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f"label[for='{selected_option_id}']"))
                )
                print("Found payment label, attempting to click...")

                # Scroll to the label
                driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", payment_label)
                time.sleep(0.5)

                # Click the label
                payment_label.click()
                time.sleep(1)

                # Verify the option was selected by checking the input
                payment_input = driver.find_element(By.ID, selected_option_id)
                if payment_input.is_selected():
                    clean_option_name = selected_option_name.lower().replace(' ', '_').replace('\\', '_')
                    take_screenshot(f"selected_{clean_option_name}")
                    print(f"Successfully selected {selected_option_name} payment option")
                    return True, selected_option_name

                else:
                    print("Label click didn't change selection state")
                    # Fallback to JavaScript click if needed
                    driver.execute_script("arguments[0].click();", payment_input)
                    time.sleep(1)
                    if payment_input.is_selected():
                        print("Successfully selected using JavaScript fallback")
                        return True, selected_option_name
                    return False, selected_option_name

            except Exception as e:
                    print(f"Failed to select payment option {selected_option_name}: {str(e)}")
                    return False, selected_option_name
        else:
                print("Using default payment option (Bank transfer), no action needed")
                return True, selected_option_name

    except Exception as e:
            print(f"Error in payment selection process: {str(e)}")
            take_screenshot("payment_option_error")
            return False, "Error"

# Create a simple step counter class
class StepCounter:
    def __init__(self):
        self.step = 1
    
    def print_step(self, message):
        print(f"\n--- Step {self.step}: {message} ---")
        self.step += 1


def fill_order_form(user_email, test_phone):
    # Fill the order form
    try:
        ship_to = choose_address() #is a dictionary
        print(f"Chosen address in: {str(ship_to['country'])}")
        
        # Wait for the form to be present
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "bx-input-order-EMAIL"))
        )
        
        print("Form found, starting to fill fields...")
        take_screenshot("form_loaded")
        
        # Contact information
        print("Filling contact information...")
        
        # Email field
        try:
            email_field = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.ID, "bx-input-order-EMAIL"))
            )
            email_field.clear()
            email_field.send_keys(user_email)
            print("✓ Email field filled")
        except Exception as e:
            print(f"✗ Error with email field: {str(e)}")
            take_screenshot("email_field_error")
            return False
        
        # Phone field
        try:
            phone_field = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.ID, "bx-input-order-PHONE"))
            )
            phone_field.clear()
            phone_field.send_keys(test_phone)
            print("✓ Phone field filled")
        except Exception as e:
            print(f"✗ Error with phone field: {str(e)}")
            take_screenshot("phone_field_error")
            return False
        
        # Name field
        try:
            name_field = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.ID, "bx-input-order-FIO_SHIP"))
            )
            name_field.clear()
            name_field.send_keys("Alena Auto Test")
            print("✓ Name field filled")
        except Exception as e:
            print(f"✗ Error with name field: {str(e)}")
            take_screenshot("name_field_error")
            return False
        
        # Order comment
        try:
            comment_field = driver.find_element(By.ID, "bx-input-order-USER_DESCRIPTION")
            driver.execute_script('arguments[0].value = "Alena Auto Test\\nThis order was made by Alyona\'s helpful minions";', comment_field)
            print("✓ Comment field filled")
        
        except Exception as e:
            print(f"✗ Error with comment field: {str(e)}")
            take_screenshot("comment_field_error")
        
        # Shipping address
        print("Filling shipping address...")
        
        # Country field (a dropdown with typeahead)
        try:
            country_field = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "bx-input-order-COUNTRY_SHIPPING-ts-control"))
            )
            country_field.click()
            country_field.clear()
            country_field.send_keys(ship_to['country'])
            # Wait a moment for the dropdown to appear and select the first option
            time.sleep(1)
            country_field.send_keys(Keys.ENTER)
            print("✓ Country selected")
            
            # Add a small delay after country selection to allow any JavaScript to process
            time.sleep(1)
            
            # Click elsewhere to ensure the country field loses focus
            driver.find_element(By.TAG_NAME, "body").click()
            time.sleep(0.5)
            
        except Exception as e:
            print(f"✗ Error with country field: {str(e)}")
            take_screenshot("country_field_error")
            return False
        
        # City field 
        try:
            # Wait for the city field to be interactable
            city_field = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "bx-input-order-CITY_SHIP"))
            )
            
            # Scroll to the element to ensure it's in view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", city_field)
            time.sleep(0.5)
            
            # Click on the field to ensure focus
            city_field.click()
            time.sleep(0.5)
            
            # Clear and fill the field
            city_field.clear()
            city_field.send_keys(ship_to['city'])
            print("✓ City field filled")
            
            # Press Tab to move to next field (this might help with form validation)
            city_field.send_keys(Keys.TAB)
            time.sleep(0.5)
            
        except Exception as e:
            print(f"✗ Error with city field: {str(e)}")
            take_screenshot("city_field_error")
            return False
        
        # Address field
        try:
            address_field = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "bx-input-order-ADDRESS_SHIP"))
            )
            
            # Click to ensure focus
            address_field.click()
            time.sleep(0.5)
            
            address_field.clear()
            address_field.send_keys(ship_to['address'])
            print("✓ Address field filled")
            
            # Press Tab to move to next field
            address_field.send_keys(Keys.TAB)
            time.sleep(0.5)
            
        except Exception as e:
            print(f"✗ Error with address field: {str(e)}")
            take_screenshot("address_field_error")
            return False
        
        # Postal code field
        try:
            postal_code_field = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "bx-input-order-ZIP_SHIP"))
            )
            
            # Click to ensure focus
            postal_code_field.click()
            time.sleep(0.5)
            
            postal_code_field.clear()
            postal_code_field.send_keys(ship_to['postal_code'])
            print("✓ Postal code field filled")
            
        except Exception as e:
            print(f"✗ Error with postal code field: {str(e)}")
            take_screenshot("postal_code_field_error")
            return False
        
        # Billing address is the same as shipping (default tick remains)
        print("Billing address remains same as shipping (default)")
        
        take_screenshot("order_form_filled")
        print("Order form filled successfully")
        return True  # CHANGED: Returns only boolean, not tuple
        
    except Exception as e:
        print(f"Error filling order form: {str(e)}")
        take_screenshot("order_form_error")
        return False  # CHANGED: Returns only boolean, not tuple

def rename_screenshots_folder(order_number):
    # Rename screenshots folder with order number
    try:
        source = "C:/Users/astavrova/Desktop/Алена (врем.)/0 - автоматизация/orders/lvh-auto-tests/daily/screenshots"
        dest = f"C:/Users/astavrova/Desktop/Алена (врем.)/0 - автоматизация/orders/lvh-auto-tests/daily/{order_number}"
        
        if os.path.exists(source):
            os.rename(source, dest)
            print(f"✓ Screenshots folder renamed to: {order_number}")
        else:
            print(f"✗ Screenshots folder not found at: {source}")
            
    except OSError as error:
        print(f"✗ Could not rename folder: {error}")
        # Create a new folder with order number anyway
        try:
            dest = f"C:/Users/astavrova/Desktop/Алена (врем.)/0 - автоматизация/orders/lvh-auto-tests/monthly/{order_number}"
            os.makedirs(dest, exist_ok=True)
            print(f"✓ Created folder: {order_number}")
        except:
            pass

def place_order():
    # Finalize the order by clicking the checkout button on the order form
    try:
        print("Placing final order...")
        
        take_screenshot("before_final_order")
        
        # Find and click the checkout button
        checkout_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "submit"))
        )
        print(f"✓ Found checkout button: '{checkout_button.text}'")
        
        # Scroll to button
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkout_button)
        time.sleep(1)
        checkout_button.click()

        # IMMEDIATELY check for JavaScript/form validation errors
        time.sleep(2)  # Give time for any JS validation to run
        
        # Check for the "already exists" error specifically
        error_found = False
        error_text = ""
        
        # Try multiple ways to find error messages
        error_selectors = [
            # By specific error text (most reliable)
            (By.XPATH, "//*[contains(text(), 'Esiste già')]"),
            
            # By CSS classes that might indicate errors
            (By.CSS_SELECTOR, ".alert-content")
        ]
        
        for by, selector in error_selectors:
            try:
                elements = driver.find_elements(by, selector)
                for elem in elements:
                    if elem.is_displayed():
                        error_text = elem.text[:100] if elem.text else "Unknown error"
                        print(f"✗ Found error: {error_text}")
                        error_found = True
                        take_screenshot(f"order_error_{by[1][:20]}")
                        break
                if error_found:
                    break
            except:
                continue
        
        if error_found:
            print("✗ Order blocked by error - NOT placed")
            return False
        
        # If no errors found, check for success
        print("No errors detected, checking for order confirmation...")
        
        # Wait a bit for potential redirect
        time.sleep(3)
        
        # Check 1: Success URL with ORDER_ID
        current_url = driver.current_url
        if "ORDER_ID=" in current_url:
            try:
                import urllib.parse
                parsed_url = urllib.parse.urlparse(current_url)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                order_number = query_params.get('ORDER_ID', [None])[0]
                
                if order_number:
                    print(f"✓ ORDER CONFIRMED! Order number: {order_number}")
                    take_screenshot("order_confirmation")
                    
                    # Handle payment popups if any
                    main_window = driver.current_window_handle
                    if len(driver.window_handles) > 1:
                        print("Closing payment popup tabs...")
                        for handle in driver.window_handles:
                            if handle != main_window:
                                driver.switch_to.window(handle)
                                driver.close()
                        driver.switch_to.window(main_window)
                    
                    # Rename screenshots folder
                    rename_screenshots_folder(order_number)
                    return order_number
            except Exception as e:
                print(f"✗️ Could not parse order number: {str(e)}")
                  
        # Check 2: Are we still on the order page? (form didn't submit)
        if "order" in current_url and "ORDER_ID=" not in current_url:
            # Check if submit button is still there
            try:
                still_exists = driver.find_elements(By.ID, "submit")
                if still_exists:
                    print("✗ Still on order page with submit button - order NOT placed")
                    take_screenshot("still_on_order_page")
                    return False
            except:
                pass
        
        # If we're unsure
        print("✗ Order status unclear after submission")
        print("Check email to confirm")
        take_screenshot("order_status_unclear")
        return False  # Be conservative
        
    except Exception as e:
        print(f"✗ Error in final order submission: {str(e)}")
        take_screenshot("final_order_error")
        return False
    
def proceed_to_checkout():
    # Click the checkout button and verify redirection Basket > Order page
    try:
        print("Looking for checkout button...")
        checkout_button = driver.find_element(By.XPATH, f"//*[contains(text(), 'Per controllare')]")
        if checkout_button and checkout_button.is_displayed():
            print(f"Found checkout button")
                                
        if not checkout_button:
            raise Exception("Could not find checkout button")
        
        # Scroll to the button if needed
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", checkout_button)
        time.sleep(1)
        
        take_screenshot("before_checkout_click")
        
        # Click the button
        print("Clicking checkout button...")
        checkout_button.click()
        
        # Wait for the order page to load
        print("Waiting for order page to load...")
        WebDriverWait(driver, 5).until(
            EC.url_contains("order")
        )
        
        # Verify we're on the order page
        current_url = driver.current_url.lower()
        if "order" in current_url:
            print(f"Successfully navigated to order page: {driver.current_url}")
            take_screenshot("order_page")
            return True
        else:
            print(f"Not on order page. Current URL: {driver.current_url}")
            take_screenshot("not_on_order_page")
            return False
        
    except Exception as e:
        print(f"Failed to proceed to checkout: {str(e)}")
        take_screenshot("checkout_error")
        return False

def calculate_expected_fees_it(item_price_eur, delivery_option, payment_option):
    """
    Calculate expected fees for Italian orders
    Returns: (delivery_fee, payment_fee, total_fee)
    """
    delivery_fee = 0
    payment_fee = 0
    
    # Delivery fee logic - CORRECTED based on your clarification
    if "Consegna standard" in delivery_option:
        if item_price_eur >= 70:
            delivery_fee = 0  # Free for orders >= 70€
        else:
            delivery_fee = 5  # Standard delivery cost for orders < 70€
    elif "Consegna espressa" in delivery_option:
        # Express delivery is 10€ for ANY order value (not added to standard)
        delivery_fee = 10
    
    # Payment fee logic
    if "In contanti alla consegna" in payment_option:
        payment_fee = 3  # Cash on delivery fee
    
    total_fee = delivery_fee + payment_fee
    
    return delivery_fee, payment_fee, total_fee

def get_shipping_price_eur():
    """Get shipping price in Euros from order page"""
    try:
        price_element = driver.find_element(By.ID, 'bx-cost-shipping')
        shipping_text = price_element.text.strip()
        
        print(f"Shipping text: '{shipping_text}'")
        
        # Check for free shipping in Italian
        if "gratuita" in shipping_text.lower() or "gratis" in shipping_text.lower():
            return 0.0
        
        return extract_price(shipping_text)
    except:
        return None

def get_total_price_order_page_eur():
    """Get total price from order page"""
    try:
        price_element = driver.find_element(By.ID, 'bx-total-cost')
        return extract_price(price_element.text)
    except Exception as e:
        print(f"Error getting total price: {str(e)}")
        return None

def verify_fees_it(item_price_eur, delivery_option, payment_option):
    """Verify fees for Italian orders"""
    try:
        print("\n=== VERIFYING ITALIAN FEES ===")
        
        # Get actual prices from page
        actual_shipping_fee = get_shipping_price_eur()
        actual_total = get_total_price_order_page_eur()
        
        print(f"Item price: {item_price_eur} €")
        print(f"Delivery option: {delivery_option}")
        print(f"Payment option: {payment_option}")
        print(f"Actual shipping fee from page: {actual_shipping_fee if actual_shipping_fee is not None else 'Not found'} €")
        print(f"Actual total from page: {actual_total if actual_total is not None else 'Not found'} €")
        
        # Calculate expected fees
        expected_delivery, expected_payment, expected_total_fee = calculate_expected_fees_it(
            item_price_eur, delivery_option, payment_option
        )
        
        # Calculate expected total
        expected_total = item_price_eur + expected_delivery + expected_payment
        
        print(f"\nExpected calculations:")
        print(f"  - Delivery fee: {expected_delivery} €")
        if expected_payment > 0:
            print(f"  - Payment fee (cash on delivery): {expected_payment} €")
        print(f"  - Total fees: {expected_total_fee} €")
        print(f"  - Expected total: {expected_total} €")
        
        # Compare with actual
        issues = []
        
        # IT WEBSITE SPECIFIC: For cash-on-delivery, shipping display includes payment fee
        if actual_shipping_fee is not None:
            if "In contanti alla consegna" in payment_option:
                # For cash-on-delivery: shipping display is the payment fee (if delivery is free)
                # or delivery + payment fee (if delivery has cost)
                expected_shipping_display = expected_delivery + expected_payment
                if abs(actual_shipping_fee - expected_shipping_display) > 0.01:
                    issues.append(f"Shipping display mismatch (cash-on-delivery): expected {expected_shipping_display} € (delivery {expected_delivery} + payment {expected_payment}), got {actual_shipping_fee} €")
                else:
                    print(f"✓ Shipping display correct: {actual_shipping_fee} €")
            else:
                # For other payment methods: shipping is just delivery fee
                if abs(actual_shipping_fee - expected_delivery) > 0.01:
                    issues.append(f"Shipping fee mismatch: expected {expected_delivery} €, got {actual_shipping_fee} €")
                else:
                    print(f"✓ Shipping fee correct: {actual_shipping_fee} €")
        else:
            issues.append("Could not get actual shipping fee from page")
        
        if actual_total is not None:
            if abs(actual_total - expected_total) > 0.01:
                issues.append(f"Total price mismatch: expected {expected_total} €, got {actual_total} €")
            else:
                print(f"✓ Total price correct: {actual_total} €")
        else:
            issues.append("Could not get actual total from page")
        
        if issues:
            print("\n✗ ISSUES FOUND:")
            for issue in issues:
                print(f"  - {issue}")
            take_screenshot("fee_verification_failed_it")
            return False, expected_delivery, expected_payment, actual_total
        else:
            print("\n✓ All fees verified correctly!")
            return True, expected_delivery, expected_payment, actual_total
            
    except Exception as e:
        print(f"Error verifying fees: {str(e)}")
        take_screenshot("fee_verification_error_it")
        return False, None, None, None

# Main execution
def main_it(email, phone):
    global driver, wait
    
    try:
        # Initialize step counter
        step_counter = StepCounter()
        print("----------LOGS FOR NERDS----------")
        user_email = email
        test_phone = phone

        print("\nLaunching browser...")
        driver = create_optimized_driver()
        driver.maximize_window()
        wait = WebDriverWait(driver, 20)
        
        # Initialize variables for summary (LIKE HU SCRIPT)
        sku = choose_sku()
        selected_delivery_option = None
        selected_payment_option = None
        order_result = None
        order_price = None
        basket_price = None
        free_shipping_result = None
        
        print(f"Chosen SKU: {str(sku)}")
        
        step_counter.print_step("Searching for SKU")
        
        if search_for_sku(sku):
            step_counter.print_step("Getting offer ID")
            offer_id = get_offer_id_for_sku(sku)
            
            if offer_id:
                step_counter.print_step("Adding to cart via API")
                
                if add_to_cart_via_api(offer_id, 1):
                    step_counter.print_step("Refreshing page to synchronize UI")
                    driver.refresh()
                    time.sleep(3)
                    step_counter.print_step("Navigating to cart")
                    
                    if navigate_to_cart_directly():
                        step_counter.print_step("Checking cart contents")
                        if check_cart_contents(sku):
                            step_counter.print_step("Getting cart total price")
                            basket_price = get_total_price()
                            
                            if basket_price is not None:
                                print(f"Cart total price: {basket_price}")
                                
                                step_counter.print_step("Proceeding to checkout")
                                if proceed_to_checkout():
                                    step_counter.print_step("Getting order page total price")
                                    order_price = get_total_price()
                                    
                                    if order_price is not None:
                                        print(f"Order page total price: {order_price}")
                                        take_screenshot("order_with_price")
                                        
                                        # Compare prices
                                        if abs(basket_price - order_price) < 0.01:  # Account for floating point precision
                                            print("✓ SUCCESS: Prices match between basket and order pages!")
                                            print(f"✓ Total price: {order_price}")

                                            step_counter.print_step("Filling order form")            
                                            form_success = fill_order_form(user_email, test_phone)  # CHANGED: Only boolean

                                            if form_success:
                                                # Store item price before fees
                                                item_price_euro = order_price
                                                
                                                # LIKE HU SCRIPT: Select delivery option
                                                step_counter.print_step("Selecting delivery option")
                                                delivery_success, selected_delivery_option = select_delivery_option()
                                                if not delivery_success:
                                                    print("✗ Delivery selection failed, but continuing with order process")
                                                
                                                # LIKE HU SCRIPT: Select payment option  
                                                step_counter.print_step("Selecting payment option")
                                                payment_success, selected_payment_option = select_payment_option(selected_delivery_option)
                                                if not payment_success:
                                                    print("✗ Payment selection failed, but continuing with order process")

                                                print("Verifying delivery and payment fees...")

                                                actual_shipping_fee = None
                                                expected_payment = None
                                                actual_total = None
                                                expected_delivery = None  # Added this
                                                fees_verified = False  # Added this

                                                if order_price is not None and selected_delivery_option and selected_payment_option:
                                                    fees_verified, expected_delivery, expected_payment, actual_total = verify_fees_it(
                                                    order_price, selected_delivery_option, selected_payment_option
                                                    )
    
                                                    # Also get the actual shipping fee for display
                                                    actual_shipping_fee = get_shipping_price_eur()
    
                                                    if fees_verified:
                                                        print("✓ Fees verified successfully")
                                                    else:
                                                        print("✗ Fee verification failed")
                                                        
                                                else:
                                                    print("✗ Could not verify fees: missing data")

                                                step_counter.print_step("Placing order")
                                                order_result = place_order()

                                                if order_result:
                                                    if isinstance(order_result, str):
                                                        print(f"✓ Order successfully placed! Order number: {order_result}")
                                                    else:
                                                        print("✓ Order successfully placed!")
                                                    print("Please check your email and 1C system for order confirmation")                                                   

                                                else:
                                                    print("❌ Failed to place order")                                                

                                            else:
                                                print("❌ Failed to fill order form") 
                                            
                                        else:
                                            print(f"❌ WARNING: Prices don't match! Basket: {basket_price}, Order: {order_price}")
                                                                                       
                                    else:
                                        print("❌ Could not extract price from order page")
                                else:
                                    print("\n❌ Failed to proceed to checkout")
                            else:
                                print("\n❌ Could not extract price from basket page")
                        else:
                            print("\n❌ Item was added but not found in cart")
                    else:
                        print("\n❌ Failed to navigate to cart")
                else:
                    print("\n❌ Failed to add item to cart via API")
            else:
                print("\n❌ Could not find offer ID for the product")
        else:
            print("\n❌ Failed to search for SKU")
        
        print("\nProcess completed. Browser will close in 10 seconds.")
        print("----------ORDER INFO----------")
        if order_result:
            if isinstance(order_result, str):
                print(f"Order number: {order_result}")
            else:
                print("Order number: Order placed (no number captured)")
        else:
            print("Order number: Order wasn't placed")
        print(f"Chosen SKU: {sku}")
        print(f"Item price: {order_price:.2f} €" if order_price else "Item price: N/A")

        # Format delivery and payment options
        delivery_display = selected_delivery_option if selected_delivery_option else 'N/A'
        payment_display = selected_payment_option if selected_payment_option else 'N/A'
        print(f"Delivery option: {delivery_display}")
        print(f"Payment option: {payment_display}")

        # Show fee breakdown based on verification results
        if fees_verified:
            print("✓ Fee verification: PASSED")
    
            # Clean formatting - always show 2 decimal places
            if expected_delivery is not None:
                print(f"  Expected delivery fee: {expected_delivery:.2f} €")
            if expected_payment is not None and expected_payment > 0:
                print(f"  Expected payment fee: {expected_payment:.2f} €")
    
            # Show what the website actually displays
            if actual_shipping_fee is not None:
                if "In contanti alla consegna" in payment_display:
                    print(f"  Website shows (combined): {actual_shipping_fee:.2f} €")
                else:
                    print(f"  Website shows: {actual_shipping_fee:.2f} €")
    
            if actual_total is not None:
                print(f"Total price: {actual_total:.2f} €")
            else:
                print("Total price: N/A")
        
        else:
            print("✗ Fee verification: FAILED")
            if actual_shipping_fee is not None:
                print(f"  Website shows: {actual_shipping_fee:.2f} €")
            if actual_total is not None:
                print(f"  Total price: {actual_total:.2f} €")

        print("----------END----------")
        time.sleep(3)
        
    except Exception as e:
        print(f"\n❌ Script failed with error: {str(e)}")
        take_screenshot("main_script_error")          
   
    finally:
        driver.quit()

if __name__ == "__main__":
    main_it()
