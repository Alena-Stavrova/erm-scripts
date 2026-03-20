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
import traceback
import sys

# Initialize driver with None (to be changed later)
driver = None
wait = None
website_main = "https://de.ermenrich.com/"

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

def take_screenshot(name):
    # Create screenshot folder, name screenshot images
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    filename = f"screenshots/{name}_{int(time.time())}.png"
    driver.save_screenshot(filename)
    print(f"(Screenshot saved as: {filename})")
    return filename

# Step counter class to count step number automatically
class StepCounter:
    def __init__(self):
        self.step = 1
    
    def print_step(self, message):
        print(f"\n--- Step {self.step}: {message} ---")
        self.step += 1
    
# Choose random SKU:
def choose_sku():
    # First 5 are under 70 EU, last 5 are 70+
    skus = [83836, 83820, 84547, 84545, 83089, 84558, 84638, 84087, 82544, 85574]
    sku_num = random.randint(0,9)
    sku = skus[sku_num]
    return sku

def choose_address():
    shipping_addresses = [
        {
            'country': 'Deutschland',
            'city': 'Gmund am Tegernsee',
            'address': 'Riedersteinweg 3',
            'postal_code': '83703'
        },
        {
            'country': 'Deutschland',
            'city': 'Bielefeld',
            'address': 'Ziegelstrasse 7',
            'postal_code': '33607'
        },
        {
            'country': 'Deutschland',
            'city': 'Kiel',
            'address': 'August-Sievers-Ring 26',
            'postal_code': '24148'
        }
]
    addresses = shipping_addresses[random.randint(0,2)]
    return(addresses)   # Returns a dictionary

def extract_price(price_text):
    # Extract numeric price from text
    # Remove currency symbols, spaces and other non-numeric chars except decimal point
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
        price_element = driver.find_element(By.CLASS_NAME, 'cart-panel__result-price')
        price_text = price_element.text
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
        time.sleep(3)

        close_cookie_popup()
       
        print("Opening search box...")
        search_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".header__search")))
        search_box.click()
        time.sleep(1)

        print("Entering SKU...")
        search_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[placeholder*="uchen"]')))
        search_input.clear()
        search_input.send_keys(str(sku))

        print("Submitting search...")
        search_input.send_keys(Keys.ENTER)

        print("Waiting for results to load...")
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".product-card")))
        except:
            time.sleep(5)

        print("Search completed successfully")
        return True

    except Exceptions as e:
        print(f"Search failed: {str(e)}")
        take_screenshot("search_error")
        return False

def get_offer_id_for_sku(sku):
    # Extract the offerID for the product with the given SKU
    try:
        print("Finding product offer ID...")

        # Find the product card that contains our SKU
        sku_element = wait.until(EC.visibility_of_element_located(
            (By.XPATH, f"//*[contains(text(), 'ID {sku}')]"))
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
    # Add item to card using the direct API call
    try:
        print("Adding item to cart via API...")

        # Execute JS to make the API call
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

        # Execute JS
        driver.execute_script(script)

        # Wait for the UI to update
        time.sleep(3)
        print("API call completed successfully")
        return True

    except Exception as e:
        print(f"Failed to add to cart via API: {str(e)}")
        take_screenshot("api_add_error")
        return False

def navigate_to_cart_directly():
    # Navigate to the cart page directly by URL
    try:
        cart_url = "https://de.ermenrich.com/basket/"
        print(f"Navigating to cart URL: {cart_url}")

        driver.get(cart_url)
        time.sleep(3)

        # Check if we're on a cart page
        current_url = driver.current_url.lower()
        if "basket" in current_url:
            print("Successfully navigated to cart page")
            return True
        else:
            print(f"Not on cart page. Current URL: {driver.current_url}")
            return False

    except Exception as e:
        print(f"Failed to navigate to cart: {str(e)}")
        take_screenshot("cart_navigation_error")
        return False

def check_cart_contents(sku):
    # Check if the cart has our item
    print("Checking cart contents...")
    try:
        sku_element = driver.find_element(By.XPATH, f"//*[contains(text(), 'ID: {sku}')]")
        take_screenshot("cart_with_our_item")
        return True

    except Exception as e:
        print(f"Error checking cart contents: {str(e)}")
        take_screenshot("cart_check_error")
        return False

def select_payment_option():
    # Randomly select a payment option for orders over 70€ using element IDs
    try:
        print("Selecting payment option...")

        # Define payment options with their corresponding IDs (equal probability)
        payment_options = {
            "Überweisung": "ID_PAY_SYSTEM_ID_32",
            "Kredit-/EC-Karte": "ID_PAY_SYSTEM_ID_45",
            "PayPal": "ID_PAY_SYSTEM_ID_33"
        }

        # Randomly select any payment option
        selected_option_name = random.choice(list(payment_options.keys())) # Random choice within keys of payment_options dictionary
        selected_option_id = payment_options[selected_option_name]

        print(f"Selected payment option: {selected_option_name} (ID: {selected_option_id})")

        #Only interact with the UI if it's not the default option
        if selected_option_name != "Überweisung":
            # Find and click the payment option using its ID
            try:
                # Find and click the label of the payment option
                payment_label = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, f"label[for='{selected_option_id}']"))
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
                    clean_option_name = selected_option_name.lower().replace(' ', '_').replace('/', '_')
                    take_screenshot(f"selected_{clean_option_name}")
                    print(f"Successfully selected {selected_option_name} payment option")
                    return True, selected_option_name
                    
                else:
                    print("Label click didn't change selection state")
                    # Fallback to JS click if needed
                    driver.execute_script("arguments[0].click();", payment_input)
                    time.sleep(1)
                    if payment_input.is_selected():
                        print("Successfully selected using JS fallback")
                        return True, selected_option_name
                    return False, selected_option_name
                
            except Exception as e:
                print(f"Failed to select payment option {selected_option_name}: {str(e)}")
                return False, selected_option_name
            
        else:
            print("Using default payment option (Überweisung), no action needed")
            return True,  selected_option_name
        
    except Exception as e:
        print(f"Error in payment selection process: {str(e)}")
        take_screenshot("payment_option_error")
        return False, "Error"

def fill_order_form(user_email, test_phone):
    try:
        ship_to = choose_address() #is a dictionary
        print(f"Chosen address in: {str(ship_to['city'])}")
        
        # Wait for the form
        WebDriverWait(driver, 15).until(EC.presence_of_element_located(
            (By.ID, "bx-input-order-EMAIL"))
        )
        print("Form found, starting to fill fields...")

        # Contact information
        print("Filling contact information...")

        # Email field
        try:
            email_field = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "bx-input-order-EMAIL")))
            email_field.clear()
            email_field.send_keys(user_email)
            print("✓ Email field filled")
        except Exception as e:
            print(f"✗ Error with email field: {str(e)}")
            take_screenshot("email_field_error")
            return False

        #Phone field
        try:
            phone_field = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "bx-input-order-PHONE")))
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

        # Country field
        try:
            country_field = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "bx-input-order-COUNTRY_SHIPPING-ts-control")))
            country_field.click()
            country_field.clear()
            country_field.send_keys(ship_to['country'])
            # Wait a moment for the dropdown to appear and select the first option
            time.sleep(1)
            country_field.send_keys(Keys.ENTER)
            print("✓ Country selected")

            # Add a small delay after country selection to allow any JS to process
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
            city_field = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "bx-input-order-CITY_SHIP")))

            # Scroll to the element to ensure it's in view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", city_field)
            time.sleep(0.5)

            # Click on the field to ensure focus
            city_field.click()
            time.sleep(0.5)

            # Clear  and fill the field
            city_field.clear()
            city_field.send_keys(ship_to['city'])
            print("✓ City field filled")

            # Press Tab to move to the next field (this might help with form validation)
            city_field.send_keys(Keys.TAB)
            time.sleep(0.5)

        except Exception as e:
            print("✗ Error with city field: {str(e)}")
            take_screenshot("city_field_error")
            return False

        # Address field
        try:
            address_field = WebDriverWait(driver, 5). until(EC.element_to_be_clickable((By.ID, "bx-input-order-ADDRESS_SHIP")))

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
            postal_code_field = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "bx-input-order-ZIP_SHIP")))

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
        print("Billing address remains the same as shipping (default)")

        # Check delivery options
        print("Checking delivery options...")
        try:
            # Look for the specific courier delivery option
            courier_option = driver.find_elements(By.CSS_SELECTOR, "label[for='ID_SHIPPING_METHOD_ID_16']")

            if len(courier_option) == 1:
                print("Found 1 delivery option as expected (Kurierzustellung)")
            elif len(courier_option) > 1:
                print(f"WARNING: Found {len(courier_option)} delivery options, expected only 1 (Kurierzustellung)")
            else:
                print("Could not find the Kurierzustellung delivery option")

        except Exception as e:
            print(f"Could not check delivery options: {str(e)}")
            
        take_screenshot("order_form_filled")
        print("Order form filled successfully")
        return True

    except Exception as e:
        print(f"Error filling order form: {str(e)}")
        take_screenshot("order_form_error")
        return False

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
        print("Placing order...")
        
        take_screenshot("before_place_order")
        
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
            (By.XPATH, "//*[contains(text(), 'besteht bereits')]"),
            
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
                print(f"✗ Could not parse order number: {str(e)}")

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
    # Click the checkout button and verify redirection to order page
    try:
        print("Looking for checkout button...")
        checkout_button = driver.find_element(By.XPATH, f"//*[contains(text(), 'Zur Kasse')]")
        if checkout_button and checkout_button.is_displayed():
            print(f"Found checkout button")

        if not checkout_button:
            raise Exception("Could not find checkout button...")

        # Scroll to the button if needed
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", checkout_button)
        time.sleep(1)

        take_screenshot("before_checkout_click")

        # Click the button
        print("Clicking checkout button...")
        checkout_button.click()

        # Wait for the order page to load
        print("Waiting for order page to load...")
        WebDriverWait(driver, 15).until(
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

def verify_free_shipping():
    # Verify that free shipping is applied for orders over 70€
    try:
        print("Verifying free shipping...")
        
        # Wait a moment for the page to update after address entry
        time.sleep(2)
        
        # Look for the free shipping element
        free_shipping_element = wait.until(
            EC.presence_of_element_located((By.ID, "bx-cost-shipping"))
        )
        
        # Check if the element contains "Free shipping" text
        if "Kostenloser Versand" in free_shipping_element.text:
            print("✓ Free shipping verified successfully!")
            return True
        else:
            print(f"✗ Free shipping not applied. Shipping cost: {free_shipping_element.text}")
            take_screenshot("shipping_cost_error")
            return False
            
    except Exception as e:
        print(f"Error verifying free shipping: {str(e)}")
        take_screenshot("free_shipping_verification_error")
        return False

# Main execution
def main_de(email, phone):
    global driver, wait
    
    try:
        # Initialize step counter
        step_counter = StepCounter()
        print("---------------LOGS FOR NERDS---------------")
        user_email = email
        test_phone = phone

        print("\nLaunching browser...")
        driver = create_optimized_driver()
        driver.maximize_window()
        wait = WebDriverWait(driver, 20)

        # Initialize all variables
        delivery_option = 'Kurierzustellung'
        sku = choose_sku()
        payment_option_for_summary = "Default"  
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
                            step_counter.print_step("Getting basket total price")
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
                                        if abs(basket_price - order_price) < 0.01: # Account for floating point precision
                                            print("✓ SUCCESS: Prices match between cart and order pages!")
                                            print(f"✓ Total price: {order_price}")

                                            if fill_order_form(user_email, test_phone):
                                            # Check if order value is over 70€ and select payment option if needed

                                                if order_price >= 70:
                                                    step_counter.print_step("Verifying free shipping")                        

                                                    # Store the result instead of just calling it
                                                    free_shipping_result = verify_free_shipping()
                                                    if not free_shipping_result:
                                                        print("✗ Free shipping verification failed, but continuing with order")       



                                                    step_counter.print_step("Selecting payment option")
                                                    payment_success, chosen_payment_option = select_payment_option()
                                                    if not payment_success:
                                                        print("✗ Payment selection failed, but continuing with order process")
                                                    payment_option_for_summary = chosen_payment_option # <-- UPDATE

                                                else:
                                                    print("Order value below 70€, using default payment option")
                                                    payment_option_for_summary = "TBD (default for <70€)"  # <-- SET


                                                step_counter.print_step("Placing order")
                                                order_result = place_order()

                                                if order_result:
                                                    if isinstance(order_result, str):
                                                        print(f"✓ Order successfully placed! Order number: {order_result}")
                                                    else:
                                                        print("✓ Order successfully placed!")                                                                                                      

                                                else:
                                                    print("✗ Failed to place order")  
                                                
                                            else:
                                                print("✗ Failed to fill order form")
                                            
                                        else:
                                            print(f"✗ WARNING: Prices don't match! Cart: {basket_price}, Order: {order_price}")

                                    else:
                                        print("✗ Could not extract price from order page")

                                else:
                                    print("\n✗ Failed to proceed to checkout")
                                
                            else:
                                print("\n✗ Could not extract price from cart page")

                        else:
                            print("\n✗ Item was added but not found in cart")

                    else:
                        print("\n✗ Failed to navigate to cart")

                else:
                    print("\n✗ Failed to add item to cart via API")

            else:
                print("\n✗ Could not find offer ID for the product")

        else:
            print("\n✗ Failed to search for SKU")

        print("\nProcess completed. Browser will close in 10 seconds.")
        print("----------ORDER INFO----------")
        if order_result:
            print(f"Order number: {order_result}")
        else:
            print("Order number: order wasn't placed")
        print(f"Chosen SKU: {str(sku)}")
        print(f"Item price: {order_price if order_price else 'N/A'} €")
        print(f"Delivery option: {delivery_option}")
        print(f"Payment option: {payment_option_for_summary}")
        
        # Price match check
        if basket_price and order_price:
            if abs(basket_price - order_price) < 0.01:
                print("Cart and order prices match: ✓ Yes")
            else:
                print(f"Cart and order prices match: ✗ No (Cart: {basket_price}, Order: {order_price})")
        else:
            print("Cart and order prices match: N/A (missing price data)")
        
        if order_price and order_price >= 70:
            if free_shipping_result is True:
                print("Free delivery: ✓ Yes")
            elif free_shipping_result is False:
                print("Free delivery: ✗ No")
            else:
                print("Free delivery: Not checked")
        else:
            print("Free delivery: Not applicable (order <70€)")
        
        print("----------END----------")
        time.sleep(10)
        
    except Exception as e:
        print(f"\n✗ Script failed with error: {str(e)}")
        take_screenshot("main_script_error")

    finally:
        driver.quit()
   
if __name__ == "__main__":
    main_de()
                            
                            
                                
                                              
                                                  
              
        
    
                                        
                                                                       
          
            
            
            
        
            
                                                         
                                
              

        
        

                
                    
                    

                  
                                                                        
        


            

            


        

    


    
        
        
                                          
                                            
                                            
    



















