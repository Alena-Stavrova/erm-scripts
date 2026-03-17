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

def create_optimized_driver():
    # Create a Chrome driver optimized for speed
    options = Options()
    options.page_load_strategy = 'eager'
    
    # AGGRESSIVE image blocking
    prefs = {"profile.managed_default_content_settings.images": 1}
    options.add_experimental_option("prefs", prefs)

    # All the performance flags
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-extensions')
    options.add_argument('--no-sandbox')

    # ENABLE CACHE
    options.add_argument('--enable-disk-cache')
    options.add_argument('--disk-cache-size=104857600')
    options.add_argument('--disable-clear-browsing-data')
    
    driver = webdriver.Chrome(options=options)
    
    # LONGER timeout for initial load
    driver.set_page_load_timeout(60)
    
    return driver

# Initialize driver and wait
user_email = input("Enter email: ")
driver = create_optimized_driver()
driver.maximize_window()
wait = WebDriverWait(driver, 5)
website_main = "https://cz.ermenrich.com/"
test_phone = "+79444444444"

# Choose random sku
def choose_sku():
    skus = [83088, 83820, 84547, 84545, 83089, 84652, 84648, 86291, 83839, 84550] #first 5 are under 3000 CZK, last 5 are over
    sku_num = random.randint(0,9)
    sku = skus[sku_num]
    return(sku)

def choose_address():
    # Define a list of shipping addresses
    shipping_addresses = [
    {
        'country': 'Česká republika',
        'city': 'Praha',
        'address': 'V Nových domcích 661/10',
        #'phone': '+420777775127',
        'postal_code': '102 00'
    },
    {
        'country': 'Česká republika',
        'city': 'Brno', 
        'address': 'Zborovská 937/1',
        #'phone': '+420542213531',
        'postal_code': '616 00'
    },
    {
        'country': 'Česká republika',
        'city': 'Pardubice',
        'address': 'Ve Stezkách 215',
        #'phone': '+420212812811',
        'postal_code': '530 03'
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
    # Extract the total price - Cart page
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
        # Wait a bit for popup to appear
        time.sleep(1)
        
        # Try multiple selectors for cookie popup buttons
        accept_selectors = [
            ".cky-btn.cky-btn-accept",
            ".cookie-popup .accept",
            "[aria-label*='cookie'] button",
            "button:contains('Akceptuj')",
            "button:contains('Accept')"
        ]
        
        for selector in accept_selectors:
            try:
                accept_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                if accept_buttons:
                    # Try JavaScript click first (more reliable)
                    driver.execute_script("arguments[0].click();", accept_buttons[0])
                    print("Cookie popup closed (via JavaScript)")
                    time.sleep(0.5)
                    return True
            except:
                continue
        
        print("No cookie popup found or already closed")
        return True
    
    except Exception as e:
        print(f"Error handling cookie popup: {str(e)}")
        return False
    
def search_for_sku(sku):
    # Search for a specific SKU on the website
    try:
        print("Navigating to main page...")
        start_time = time.time()
        driver.get(website_main)
        load_time = time.time() - start_time
        print(f"Page loaded in {load_time:.1f}s")

        # If it took more than 10 seconds, warn
        if load_time > 10:
            print("⚠️  WARNING: Slow network detected")       

        close_cookie_popup()
        
        print("Opening search box...")
        search_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".header__search")))
        search_box.click()
        time.sleep(1)
        
        print("Entering SKU...")
        search_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[placeholder*="yhledat"]')))
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
    # Add item to cart using the direct API call
    try:
        print("Adding item to cart via API...")
        
        # Execute JavaScript to make the API call
        script = f"""
            // Simple API call without UI updates
            fetch('/rest/methods/user/basket/change', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }},
                body: JSON.stringify({{offerId: {offer_id}, quantity: {quantity}}})
            }}).catch(error => console.log('API error:', error));
        """
        
        # Execute the JavaScript
        driver.execute_script(script)
        time.sleep(0.5)
        print("API call completed successfully")
        return True
        
    except Exception as e:
        print(f"Failed to add to cart via API: {str(e)}")
        take_screenshot("api_add_error")
        return False

def navigate_to_cart_directly():
    # Navigate to the cart page directly by URL
    try:
        cart_url = "https://cz.ermenrich.com/basket/"
        print(f"Navigating to cart URL: {cart_url}")
        
        driver.get(cart_url)
        time.sleep(1)
        
        # Check if we're on a cart page
        current_url = driver.current_url.lower()
        if "basket" in current_url:
            print("Successfully navigated to cart page")
            return True
        else:
            print(f"Not on basket page. Current URL: {driver.current_url}")
            return False
        
    except Exception as e:
        print(f"Failed to navigate to cart: {str(e)}")
        take_screenshot("cart_navigation_error")
        return False

def check_cart_contents(sku):
    # Check if the cart has our specific item
    print("Checking cart contents...")
    try:
        sku_element = driver.find_element(By.XPATH, f"//*[contains(text(), 'ID: {sku}')]")
        take_screenshot("cart_with_our_item")
        return True
            
    except Exception as e:
        print(f"Error checking cart contents: {str(e)}")
        take_screenshot("cart_check_error")
        return False

def select_ppl_delivery():
    # Select PPL parcel box delivery with pickup point
    try:
        print("Selecting PPL delivery method...")
        
        # Step 1: Select PPL delivery method
        ppl_selector = "label[for='ID_SHIPPING_METHOD_ID_99']"
        
        ppl_element = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ppl_selector))
        )
        ppl_element.click()
        print("✓ PPL delivery selected")
        time.sleep(1)  # Wait for PPL points to load
        
        # Step 2: Select a PPL pickup point
        print("Selecting PPL pickup point...")
        
        # Wait for pickup points to appear
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".result__item-title"))
        )
        
        # Get all pickup points
        pickup_points = driver.find_elements(By.CSS_SELECTOR, ".result__item-title")
        print(f"Found {len(pickup_points)} PPL pickup points")
        
        if not pickup_points:
            print("✗ No PPL pickup points found")
            return False
        
        # Choose a random pickup point
        chosen_point = random.choice(pickup_points)
        point_name = chosen_point.text
        print(f"Selecting pickup point: {point_name}")
        
        # Click the pickup point
        chosen_point.click()
        print("✓ Pickup point clicked, waiting for details to load...")
        time.sleep(1)
        
        # Step 3: Click the "Vybrat toto místo" button
        print("Looking for selection button...")
        
        select_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Vybrat toto místo')]"))
        )
        
        print(f"Button text: '{select_button.text}'")
        select_button.click()
        print("✓ Selection button clicked")
        
        # Wait for confirmation
        time.sleep(2)
        
        # Verify selection was successful
        try:
            # Look for confirmation that the pickup point was selected
            success_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Vybráno')]")
            if success_elements:
                print("✓ Pickup point selection confirmed")
        except:
            print("✗ Could not verify selection visually, but proceeding")
        
        print("✓ PPL pickup point selected successfully")
        return True
        
    except Exception as e:
        print(f"Error selecting PPL delivery: {e}")
        return False

def select_payment_option():
    # Select random payment method
    try:
        print("Selecting payment option...")
        
        payment_options = {
            "Dobírka": "ID_PAY_SYSTEM_ID_10",
            "Online platba kartou": "ID_PAY_SYSTEM_ID_44", 
            "PayPal": "ID_PAY_SYSTEM_ID_6"
        }
        
        selected_option_name = random.choice(list(payment_options.keys()))
        selected_option_id = payment_options[selected_option_name]
        selected_option_selector = f"label[for='{selected_option_id}']"
        
        print(f"Selected payment option: {selected_option_name} (ID: {selected_option_id})")
          
        payment_element = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selected_option_selector))
        )
        payment_element.click()
        time.sleep(1)
        print("✓ Payment selected successfully")
        return True, selected_option_name
        
    except Exception as e:
        print(f"Error selecting payment: {e}")
        return False, "Failed"

def handle_czech_delivery():
    # Handle Czech delivery selection (returns success, option_name)
    try:
        print("Selecting CZ delivery option...")
        
        delivery_methods = {
            "courier": "label[for='ID_SHIPPING_METHOD_ID_3']",
            "shop_pickup": "label[for='ID_SHIPPING_METHOD_ID_4']", 
            "ppl_parcel_box": "label[for='ID_SHIPPING_METHOD_ID_99']"
        }

        # Choose delivery method
        chosen_delivery = random.choice(list(delivery_methods.keys()))
        print(f"Selected delivery method: {chosen_delivery}")

        # Map to human-readable names
        delivery_names = {
            "courier": "Doručení kurýrem",
            "shop_pickup": "Vyzvednutí",
            "ppl_parcel_box": "PPL Parcel Box"
        }
        delivery_option_name = delivery_names[chosen_delivery]        
        
        # Select the delivery option
        delivery_selector = delivery_methods[chosen_delivery]
        delivery_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, delivery_selector))
        )
        delivery_element.click()
        print(f"✓ Selected: {delivery_option_name}")
        time.sleep(2)
        
        if chosen_delivery == "ppl_parcel_box":
            delivery_success = select_ppl_delivery()
        elif chosen_delivery == "shop_pickup":
            # Click shop pickup button
            try:
                shop_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-set-shop][data-reseller-id='4']"))
                )
                shop_button.click()
                time.sleep(1)
                print("✓ Shop pickup selected")
                delivery_success = True
            except Exception as e:
                print(f"⚠ Could not select shop pickup: {e}")
                delivery_success = False
        else:
            delivery_success = True  # Courier needs no additional steps
        
        if delivery_success:
            return True, delivery_option_name
        else:
            return False, delivery_option_name
            
    except Exception as e:
        print(f"Error selecting CZ delivery: {e}")
        return False, "Error"


# Create a simple step counter class
class StepCounter:
    def __init__(self):
        self.step = 1
    
    def print_step(self, message):
        print(f"\n--- Step {self.step}: {message} ---")
        self.step += 1


def fill_order_form():
    try:
        ship_to = choose_address() #is a dictionary
        print(f"Chosen address in: {str(ship_to['city'])}")

        # Wait for the form to be present
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "bx-input-order-EMAIL"))
        )
        
        print("Form found, starting to fill fields...")
        take_screenshot("form_loaded")

        # CRITICAL: Close cookie popup on order page
        close_cookie_popup()
        
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
        
        # Country field (this might be a dropdown with typeahead)
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
        print("Placing final order...")
        
        take_screenshot("before_final_order")
        
        # Find and click the checkout button
        checkout_button = WebDriverWait(driver, 5).until(
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
            (By.XPATH, "//*[contains(text(), 'již existuje')]"),
            
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
        time.sleep(1)
        
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
        checkout_button = driver.find_element(By.XPATH, f"//*[contains(text(), 'Pokračovat')]")
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

def verify_free_shipping():
    # Verify that free shipping is applied for orders over 70€
    try:
        print("Verifying free shipping...")
        
        # Wait a moment for the page to update after address entry
        time.sleep(2)
        
        # Try multiple ways to find the shipping element
        try:
            # First try by ID
            free_shipping_element = driver.find_element(By.ID, "bx-cost-shipping")
        except:
            # Try by class or other selector
            try:
                free_shipping_element = driver.find_element(By.CSS_SELECTOR, ".cart-panel__price[data-price-type='shipping']")
            except:
                print("Could not find shipping element")
                return False
        
        shipping_text = free_shipping_element.text.strip()
        print(f"Shipping text found: '{shipping_text}'")
        
        # Check if the element contains "Doprava zdarma" or "0 Kč" or "0,00 Kč"
        if "zdarma" in shipping_text.lower() or "0 kč" in shipping_text.lower():
            print("✓ Free shipping verified successfully!")
            return True
        else:
            # Check if price is 0
            price = extract_price(shipping_text)
            if price == 0:
                print("✓ Free shipping verified (price is 0)!")
                return True
            else:
                print(f"✗ Shipping cost: {shipping_text}")
                take_screenshot("shipping_cost_error")
                return False
            
    except Exception as e:
        print(f"Error verifying free shipping: {str(e)}")
        take_screenshot("free_shipping_verification_error")
        return False

# Main execution
if __name__ == "__main__":
    try:
        
        start_total = time.time()
        
        # Initialize step counter
        step_counter = StepCounter()
        print("Running CZ script")
        print("---------------LOGS FOR NERDS---------------")
        
        # Initialize variables for summary
        sku = choose_sku()
        delivery_option = "Default"
        payment_option = "Default"
        free_shipping_result = "Not checked"
        order_result = None
        order_price = None
        basket_price = None
        
        print(f"Chosen SKU: {str(sku)}")
        
        step_counter.print_step("Searching for SKU")
        step_start = time.time()
        
        if search_for_sku(sku):
            print(f"✓ Search took: {time.time() - step_start:.1f}s")
            step_counter.print_step("Getting offer ID")
            step_start = time.time()
            offer_id = get_offer_id_for_sku(sku)
            print(f"✓ Get offer ID took: {time.time() - step_start:.1f}s")
            
            if offer_id:
                step_counter.print_step("Adding to cart via API")
                step_start = time.time()
                
                if add_to_cart_via_api(offer_id, 1):
                    print(f"✓ Add to cart took: {time.time() - step_start:.1f}s")    

                    step_counter.print_step("Navigating to cart")
                    step_start = time.time()
                    
                    if navigate_to_cart_directly():
                        print(f"✓ Navigate to cart took: {time.time() - step_start:.1f}s")
                        step_counter.print_step("Checking cart contents")
                        step_start = time.time()
                        
                        if check_cart_contents(sku):
                            print(f"✓ Checking cart contents took: {time.time() - step_start:.1f}s")
                            step_counter.print_step("Getting basket total price")
                            step_start = time.time()
                            basket_price = get_total_price()
                            
                            if basket_price is not None:
                                print(f"Basket total price: {basket_price}")
                                take_screenshot("basket_with_price")
                                print(f"✓ Getting basket total price took: {time.time() - step_start:.1f}s")
                                
                                step_counter.print_step("Proceeding to checkout")
                                step_start = time.time()
                                
                                if proceed_to_checkout():
                                    print(f"✓ Proceeding to checkout took: {time.time() - step_start:.1f}s")
                                    step_counter.print_step("Getting order page total price")
                                    step_start = time.time()
                                    order_price = get_total_price()
                                    
                                    if order_price is not None:
                                        print(f"✓ Getting order page total price took: {time.time() - step_start:.1f}s")
                                        print(f"Order page total price: {order_price}")
                                        take_screenshot("order_with_price")
                                        
                                        # Compare prices
                                        if abs(basket_price - order_price) < 0.01:  # Account for floating point precision
                                            print("✓ SUCCESS: Prices match between basket and order pages!")
                                            print(f"✓ Total price: {order_price}")

                                            step_counter.print_step("Filling order form")
                                            step_start = time.time()
                                            form_success = fill_order_form()

                                            if form_success:
                                                # Store item price before fees
                                                item_price_czk = order_price

                                                # Select delivery option (similar to PL/IT)
                                                step_counter.print_step("Selecting delivery option")
                                                delivery_success, delivery_option = handle_czech_delivery()  # This returns (success, option_name)
                                                if not delivery_success:
                                                    print("✗ Delivery selection failed, but continuing with order process")
    
                                                # Select payment option  
                                                step_counter.print_step("Selecting payment option")
                                                payment_success, payment_option = select_payment_option()
                                                if not payment_success:
                                                    print("✗ Payment selection failed, but continuing with order process")

                                                # Verify free shipping if applicable
                                                if order_price >= 3000:
                                                    print("✓ Order value is 3000+ CZK - checking free delivery")
                                                    free_shipping_result = "✓ Yes" if verify_free_shipping() else "✗ No"
                                                else:
                                                    print("Order value is below 3000 CZK - delivery may have additional cost")
                                                    free_shipping_result = "Not applicable (<3000 CZK)"

                                                step_counter.print_step("Placing order")
                                                order_result = place_order()

                                                if order_result:
                                                    print(f"✓ Placing order took: {time.time() - step_start:.1f}s")
                                                    if isinstance(order_result, str):
                                                        print(f"✓ Order successfully placed! Order number: {order_result}")
                                                    else:
                                                        print("✓ Order successfully placed!")
                                                    print("Please check your email and 1C system for order confirmation")
                                                else:
                                                    print("✗ Failed to place order")
                                            else:
                                                print("✗ Failed to fill Czech order form")
                                        else:
                                            print(f"✗ WARNING: Prices don't match! Basket: {basket_price}, Order: {order_price}")
                                    else:
                                        print("✗ Could not extract price from order page")
                                else:
                                    print("\n✗ Failed to proceed to checkout")
                            else:
                                print("\n✗ Could not extract price from basket page")
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
            print("Order number: Order wasn't placed")
        print(f"Chosen SKU: {sku}")
        print(f"Item price: {order_price if order_price else 'N/A'} CZK")
        print(f"Delivery option: {delivery_option}")
        print(f"Payment option: {payment_option}")
        if basket_price and order_price:
            if abs(basket_price - order_price) < 0.01:
                print("Cart and order prices match: ✓ Yes")
            else:
                print(f"Cart and order prices match: ✗ No (Basket: {basket_price}, Order: {order_price})")
        else:
            print("Cart and order prices match: N/A (missing price data)")
        print(f"Free delivery: {free_shipping_result}")
        print("----------END----------")
        time.sleep(3)
        
    except Exception as e:
        print(f"\n❌ Script failed with error: {str(e)}")
        take_screenshot("main_script_error")        
   
    finally:
        driver.quit()


