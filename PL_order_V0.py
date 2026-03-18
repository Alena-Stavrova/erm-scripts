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
website_main = "https://pl.ermenrich.com/"

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
    # First 5 under 315, second 5 315+ zl
    skus = [83088, 83820, 84547, 84545, 83089, 84652, 84648,  86291, 84554, 84550] 
    sku_num = random.randint(0,9)
    sku = skus[sku_num]
    return(sku)

def choose_address():
    # Define a list of shipping addresses
    shipping_addresses = [
    {
        'country': 'Polska',
        'city': 'Warszawa',
        'address': 'gen. Leopolda Okulickiego 8',
        'postal_code': '03-984'
    },
    {
        'country': 'Polska',
        'city': 'Kraków', 
        'address': 'Komandosów 7',
        'postal_code': '30-334'
    },
    {
        'country': 'Polska',
        'city': 'Gdańsk',
        'address': 'Ogarna 30',
        'postal_code': '80-826'
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
        driver.get(website_main)
        time.sleep(2)

        close_cookie_popup()
        
        print("Opening search box...")
        search_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".header__search")))
        search_box.click()
        time.sleep(1)
        
        print("Entering SKU...")
        search_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[placeholder*="yszukaj"]')))
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
            (By.XPATH, f"//*[contains(text(), 'SKU {sku}')]"))
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
        cart_url = "https://pl.ermenrich.com/basket/"
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
        sku_element = driver.find_element(By.XPATH, f"//*[contains(text(), 'SKU: {sku}')]")
        take_screenshot("cart_with_our_item")
        return True
            
    except Exception as e:
        print(f"Error checking cart contents: {str(e)}")
        take_screenshot("cart_check_error")
        return False

def select_inpost_delivery():
    # Select delivery to InPost Paczkomaty for PL
    try:
        print("Selecting InPost Paczkomaty delivery method...")
        
        # Step 1: Wait for the TomSelect dropdown to be ready
        print("Waiting for city dropdown to load...")
        time.sleep(2)
        
        # Step 2: Find the city dropdown (TomSelect input)
        city_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "tomselect-2-ts-control"))
        )
        
        # Step 3: Select a city (choose from big cities with many points)
        big_cities = ["Warszawa", "Kraków", "Gdańsk", "Wrocław", "Poznań"]
        selected_city = random.choice(big_cities)
        
        print(f"Selecting city: {selected_city}")
        
        # Step 4: Clear any existing selection first
        city_input.click()
        time.sleep(0.5)
        
        # Check if there's already a selected city and clear it
        try:
            # Look for the close/clear button (×) that appears when a city is selected
            clear_buttons = driver.find_elements(By.CSS_SELECTOR, ".ts-control .item + .clear-button, .ts-control .remove")
            if clear_buttons:
                clear_buttons[0].click()
                time.sleep(0.5)
        except:
            pass
        
        # Step 5: Type the city name and wait for dropdown
        city_input.send_keys(selected_city)
        time.sleep(2)
        
        # Step 6: Select the city        
        try:
            dropdown_options = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ts-dropdown .option"))
            )
            
            exact_match_found = False
            for option in dropdown_options:
                option_text = option.text.strip()
                if option_text.lower() == selected_city.lower():
                    print(f"Found exact match: {option_text}")
                    # Click with JavaScript to ensure event fires
                    driver.execute_script("arguments[0].click();", option)
                    exact_match_found = True
                    break
            
            if not exact_match_found:
                print(f"⚠ No exact match found for '{selected_city}', using first option")
                city_input.send_keys(Keys.ENTER)
                
            else:
                print(f"✓ City '{selected_city}' selected exactly")
                
        except Exception as e:
            print(f"⚠ Could not find dropdown options: {e}. Pressing Enter as fallback.")
            city_input.send_keys(Keys.ENTER)
            
        # Wait for API call to complete and points to load
        print("Waiting for pickup points to load...")
        time.sleep(3)  # Increased from 2

        # Check for loading state
        try:
            # Wait for any loading state to clear
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("""
                    return !document.querySelector('.loading, .spinner, .ajax-loading') || 
                       document.querySelector('.loading, .spinner, .ajax-loading').style.display === 'none';
                        """)
                    )
        except:
            pass
        
        try:
            # First wait for spinner to appear (if it exists)
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".loading, .spinner, [class*='loading'], .loader, [aria-busy='true']"))
            )
            print("Spinner detected, waiting for it to disappear...")
    
            # Then wait for it to disappear
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".loading, .spinner, [class*='loading'], .loader, [aria-busy='true']"))
            )
            print("✓ Spinner disappeared")
            
        except:
            print("No spinner detected or already gone")
            pass

        # Wait for at least some points to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button.btn.btn-primary-light.w-100[data-reseller-id]"))
        )
        time.sleep(2)  # Extra wait for all points to render
        
        # Step 7: Find all pickup point buttons 
        pickup_buttons = driver.find_elements(By.CSS_SELECTOR, "button.btn.btn-primary-light.w-100[data-reseller-id]")
        
        print(f"Found {len(pickup_buttons)} pickup point buttons")
        
        if len(pickup_buttons) == 0:
            print("✗ No pickup points found!")
            take_screenshot("no_pickup_points")
            return False
        
        # Step 8: Choose a random point
        chosen_button = random.choice(pickup_buttons)
        point_id = chosen_button.get_attribute("data-reseller-id")
        point_text = chosen_button.text[:50] if chosen_button.text else "no text"
        print(f"Selected point: ID={point_id}, Text='{point_text}'")

        # Scroll into view and click with JavaScript
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", chosen_button)
        time.sleep(0.5)

        # Click with JavaScript to ensure all events fire
        #driver.execute_script("arguments[0].click();", chosen_button)
        chosen_button.click()
        print(f"✓ Clicked pickup point: {point_id}")
        time.sleep(1)

        # Verify selection was successful
        try:
            # Look for confirmation that the pickup point was selected
            success_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Zmień')]")
            if success_elements:
                print("✓ Pickup point selection confirmed")
        except:
            print("✗ Could not verify selection visually, but proceeding")
        
        print("✓ InPost pickup point selected successfully")
        return True

        """# Step 9: Verify selection COMPLETELY
        try:
            # Wait for the button to change to "Zmień"
            zmien_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-remove-shop]"))
            )

            if zmien_button.is_displayed() and "Zmień" in zmien_button.text:
                print("✓ InPost selection confirmed (button changed to 'Zmień')")
                return True
            else:
                print(f"⚠ Button found but text is: {zmien_button.text}")
                return False
                
        except Exception as e:
            print(f"⚠ Could not confirm selection with 'Zmień' button: {e}")"""
            

    except Exception as e:
        print(f"Error selecting InPost delivery: {e}")
        take_screenshot("inpost_selection_error")
        return False

def select_payment_option():
    # Select random payment method
    try:
        print("Selecting payment option...")
        
        payment_options = {
            "Przelewy": "ID_PAY_SYSTEM_ID_14",
            "Opłata za pobraniem": "ID_PAY_SYSTEM_ID_25", 
            "PayPal": "ID_PAY_SYSTEM_ID_12"
        }
        
        selected_option_name = random.choice(list(payment_options.keys()))
        selected_option_id = payment_options[selected_option_name]
        selected_option_selector = f"label[for='{selected_option_id}']"
        
        print(f"Selected payment option: {selected_option_name} (ID: {selected_option_id})")
          
        payment_element = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selected_option_selector))
        )
        payment_element.click()
        print("✓ Payment selected successfully")
        return True, selected_option_name
        
    except Exception as e:
        print(f"Error selecting payment: {e}")
        return False, "Failed"

def handle_pl_order_complete():
    # Complete PL order handler with all delivery options
    try:
        print("Handling PL order...")
        
        # FIXED: Use correct Polish IDs
        delivery_methods = {
            "courier": "label[for='ID_SHIPPING_METHOD_ID_5']",  # Dostawa kurierem
            "shop_pickup": "label[for='ID_SHIPPING_METHOD_ID_6']",  # Odbiór osobisty w sklepie Levenhuk
            "inpost": "label[for='ID_SHIPPING_METHOD_ID_7']"  # InPost Paczkomaty
        }

        # Choose delivery method
        chosen_delivery = random.choice(list(delivery_methods.keys()))
        print(f"Selected delivery method: {chosen_delivery}")

        # Map to human-readable names
        delivery_names = {
            "courier": "Dostawa kurierem",
            "shop_pickup": "Odbiór osobisty w sklepie Levenhuk",
            "inpost": "InPost Paczkomaty"
        }
        delivery_option_name = delivery_names[chosen_delivery]        
        
        # Select the delivery option
        delivery_selector = delivery_methods[chosen_delivery]
        delivery_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, delivery_selector))
        )
        delivery_element.click()
        print(f"✓ Selected: {delivery_option_name}")
        time.sleep(2)  # Wait for the selection to load
        
        if chosen_delivery == "inpost":
            # Now call the InPost specific function
            delivery_success = select_inpost_delivery()
            
        elif chosen_delivery == "shop_pickup":
            # Shop pickup - wait for the shop selection interface
            print("Waiting for shop selection interface...")
            time.sleep(2)
            
            try:
                # FIXED: Look for ANY shop pickup button (not hardcoded ID 49)
                # First, let's see what shops are available
                shop_buttons = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button.btn.btn-primary-light.w-100[data-set-shop]"))
                )
                
                if not shop_buttons:
                    print("✗ No shop buttons found")
                    take_screenshot("shop_pickup_no_buttons")
                    delivery_success = False
                else:
                    print(f"Found {len(shop_buttons)} shop pickup buttons")
                    
                    # Log all available shops
                    for i, btn in enumerate(shop_buttons):
                        shop_id = btn.get_attribute("data-reseller-id") or "no-id"
                        shop_text = btn.text[:50] if btn.text else "no text"
                        print(f"  Shop {i+1}: ID={shop_id}, Text='{shop_text}'")
                    
                    # Choose the first shop (usually there's only one)
                    chosen_shop = shop_buttons[0]
                    shop_id = chosen_shop.get_attribute("data-reseller-id")
                    
                    print(f"Selecting shop with ID: {shop_id}")
                    
                    # Scroll and click
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", chosen_shop)
                    time.sleep(0.5)
                    chosen_shop.click()
                    print("✓ Shop pickup button clicked")
                    
                    # Wait for confirmation
                    time.sleep(2)
                    
                    # Verify button changed to "Zmień"
                    try:
                        # Look for the same button with updated text/attributes
                        updated_shop_button = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, f"button[data-reseller-id='{shop_id}'][data-remove-shop]"))
                        )
                        if "Zmień" in updated_shop_button.text:
                            print("✓ Shop pickup confirmed (button changed to 'Zmień')")
                            delivery_success = True
                        else:
                            print(f"⚠ Shop button text: {updated_shop_button.text}")
                            delivery_success = True  # Still proceed
                    except:
                        # Fallback: look for any "Zmień" button
                        zmien_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Zmień')]")
                        if zmien_buttons:
                            print(f"✓ Found {len(zmien_buttons)} 'Zmień' buttons")
                            delivery_success = True
                        else:
                            print("⚠ Could not confirm shop selection, but proceeding")
                            delivery_success = True
                            
            except Exception as e:
                print(f"⚠ Error selecting shop pickup: {str(e)}")
                take_screenshot("shop_pickup_error")
                delivery_success = False
                
        else:
            # Courier - no additional steps needed
            delivery_success = True
        
        # Only proceed to payment if delivery was successfully configured
        if delivery_success:
            # Select payment and get the selected payment option
            payment_success, payment_option_name = select_payment_option()
            if payment_success:
                print("✓ PL order setup completed successfully!")
                return True, delivery_option_name, payment_option_name
            else:
                return False, delivery_option_name, "Failed to select payment"
        else:
            print("✗ Failed to set up delivery")
            return False, "Failed", "Not selected"
            
    except Exception as e:
        print(f"Error in PL order: {e}")
        take_screenshot("pl_order_error")
        return False, "Error", "Error"


# Create a simple step counter class
class StepCounter:
    def __init__(self):
        self.step = 1
    
    def print_step(self, message):
        print(f"\n--- Step {self.step}: {message} ---")
        self.step += 1


def fill_order_form(user_email, test_phone):
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
        
       # Country field - WITH IMPROVED HANDLING
        try:
            print("Looking for country dropdown...")
            
            # Wait for the country dropdown to be present
            country_field = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "bx-input-order-COUNTRY_SHIPPING-ts-control"))
            )
            
            # Scroll to the element
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", country_field)
            time.sleep(0.5)
            
            # Click to open dropdown
            country_field.click()
            time.sleep(1)
            
            # Type the country name
            country_field.send_keys(ship_to['country'])
            time.sleep(2)  # Wait for dropdown to populate
            
            # Try to select exact country from dropdown options
            try:
                # Look for dropdown options
                dropdown_options = driver.find_elements(By.CSS_SELECTOR, ".ts-dropdown .option")
                
                exact_match = None
                for option in dropdown_options:
                    if option.text.strip().lower() == ship_to['country'].lower():
                        exact_match = option
                        break
                
                if exact_match:
                    exact_match.click()
                    print(f"✓ Country '{ship_to['country']}' selected exactly from dropdown")
                else:
                    # Fallback: press Enter
                    country_field.send_keys(Keys.ENTER)
                    print(f"✓ Country '{ship_to['country']}' selected (Enter pressed)")
                    
            except:
                # If dropdown not found, press Enter
                country_field.send_keys(Keys.ENTER)
                print(f"✓ Country '{ship_to['country']}' selected (Enter fallback)")
            
            # Wait for any JavaScript to process
            time.sleep(1)
            
            # Click elsewhere to ensure the country field loses focus
            driver.find_element(By.TAG_NAME, "body").click()
            time.sleep(0.5)
            
        except Exception as e:
            print(f"✗ Error with country field: {str(e)}")
            take_screenshot("country_field_error")
            
            # Try alternative method using JavaScript
            try:
                print("Trying JavaScript method for country field...")
                script = f"""
                    var countryField = document.getElementById('bx-input-order-COUNTRY_SHIPPING-ts-control');
                    if (countryField) {{
                        countryField.value = '{ship_to['country']}';
                        countryField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        countryField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                """
                driver.execute_script(script)
                time.sleep(1)
                print("✓ Country set via JavaScript")
            except:
                return False
        
        # City field 
        try:
            # Wait for the city field to be interactable
            city_field = WebDriverWait(driver, 10).until(
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
            
            # Press Tab to move to next field
            city_field.send_keys(Keys.TAB)
            time.sleep(0.5)
            
        except Exception as e:
            print(f"✗ Error with city field: {str(e)}")
            take_screenshot("city_field_error")
            return False
        
        # Address field
        try:
            address_field = WebDriverWait(driver, 10).until(
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
            postal_code_field = WebDriverWait(driver, 10).until(
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
        
        # Check delivery options
        print("Entering delivery and payment options...")
        try: 
            delivery_payment_success, delivery_option_name, payment_option_name = handle_pl_order_complete()  
            if delivery_payment_success:
                print(f"✓ Delivery and payment selected: {delivery_option_name}, {payment_option_name}")
                return True, delivery_option_name, payment_option_name
            else:
                return False, "Not selected", "Not selected"
            
        except Exception as e:
            print(f"Could not check delivery options: {str(e)}")
            return False, "Error", "Error"
        
        take_screenshot("order_form_filled")
        print("Order form filled successfully")
        return True, "Unknown", "Unknown"
        
    except Exception as e:
        print(f"Error filling order form: {str(e)}")
        take_screenshot("order_form_error")
        return False, "Error", "Error"

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
        checkout_button.click()
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
            print("✗ Still on order page with submit button - order NOT placed")
            take_screenshot("still_on_order_page")
            return False

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
        checkout_button = driver.find_element(By.XPATH, f"//*[contains(text(), 'Do kasy')]")
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

def verify_pl_shipping_fees(item_price_pln, delivery_option_name):
    # Verify shipping fees for PL orders
    # Returns: (is_correct, expected_fee, actual_fee, message)
    try:
        print("\nVerifying PL shipping fees...")
        
        # Get actual shipping fee from page
        shipping_fee_element = None
        try:
            shipping_fee_element = driver.find_element(By.ID, "bx-cost-shipping")
        except:
            try:
                shipping_fee_element = driver.find_element(By.CSS_SELECTOR, ".cart-panel__price[data-price-type='shipping']")
            except:
                # Try to find by text
                try:
                    elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Dostawa') or contains(text(), 'Wysyłka')]")
                    for element in elements:
                        if "zł" in element.text:
                            shipping_fee_element = element
                            break
                except:
                    pass
        
        if not shipping_fee_element:
            print("✗ Could not find shipping fee element")
            return False, None, None, "Element not found"
        
        shipping_text = shipping_fee_element.text.strip()
        print(f"Shipping text on page: '{shipping_text}'")
        
        # Extract actual price
        actual_fee = extract_price(shipping_text)
        if actual_fee is None:
            # Check if it says "Darmowa dostawa" (free shipping)
            if "darmowa" in shipping_text.lower():
                actual_fee = 0
            else:
                print("✗ Could not extract price from shipping text")
                return False, None, None, "Could not extract price"
        
        # Calculate expected fee based on PL rules
        expected_fee = 0
        message = ""
        
        if "Odbiór osobisty" in delivery_option_name:
            # Shop pickup is always free
            expected_fee = 0
            message = "Shop pickup should be free"
        else:
            # Courier or InPost
            if item_price_pln >= 315:
                expected_fee = 0
                message = f"Free delivery for orders >= 315 PLN"
            else:
                expected_fee = 15
                message = f"15 PLN delivery for orders < 315 PLN"
        
        print(f"Expected shipping fee: {expected_fee} PLN")
        print(f"Actual shipping fee: {actual_fee} PLN")
        print(f"Rule: {message}")
        
        # Compare
        if abs(actual_fee - expected_fee) < 0.01:  # Account for floating point
            print(f"✓ Shipping fee is correct!")
            return True, expected_fee, actual_fee, message
        else:
            print(f"✗ Shipping fee mismatch! Expected {expected_fee} PLN, got {actual_fee} PLN")
            take_screenshot("shipping_fee_mismatch")
            return False, expected_fee, actual_fee, message
            
    except Exception as e:
        print(f"Error verifying shipping fees: {str(e)}")
        take_screenshot("shipping_fee_verification_error")
        return False, None, None, f"Error: {str(e)}"

# Main execution
def main_pl(email, phone):
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
        
        if search_for_sku(sku):
            step_counter.print_step("Getting offer ID")
            offer_id = get_offer_id_for_sku(sku)
            
            if offer_id:
                step_counter.print_step("Adding to cart via API")
                if add_to_cart_via_api(offer_id, 1):
                    step_counter.print_step("Navigating to cart")
                   
                    if navigate_to_cart_directly():
                        step_counter.print_step("Checking cart contents")
                        
                        if check_cart_contents(sku):
                            step_counter.print_step("Getting basket total price")
                            basket_price = get_total_price()
                            
                            if basket_price is not None:
                                print(f"Basket total price: {basket_price}")
                                take_screenshot("basket_with_price")
                                                                
                                step_counter.print_step("Proceeding to checkout")
                                
                                if proceed_to_checkout():
                                    step_counter.print_step("Getting order page total price")
                                    order_price = get_total_price()
                                    
                                    if order_price is not None:
                                        print(f"Order page total price: {order_price}")
                                        take_screenshot("order_with_price")
                                        
                                        # Compare prices
                                        if abs(basket_price - order_price) < 0.01:
                                            print("✓ SUCCESS: Prices match between basket and order pages!")
                                            print(f"✓ Total price: {order_price}")

                                            step_counter.print_step("Filling order form")
                                            form_success, delivery_option, payment_option = fill_order_form(user_email, test_phone)

                                            if form_success:
                                                # Verify shipping fees according to PL rules
                                                if order_price is not None and delivery_option != "Default":
                                                    fee_correct, expected_fee, actual_fee, fee_message = verify_pl_shipping_fees(order_price, delivery_option)
                                                    
                                                    if fee_correct:
                                                        if expected_fee == 0:
                                                            free_shipping_result = "✓ Free (correct)"
                                                        else:
                                                            free_shipping_result = f"✓ {expected_fee} PLN (correct)"
                                                    else:
                                                        if expected_fee is not None and actual_fee is not None:
                                                            free_shipping_result = f"✗ Error: expected {expected_fee} PLN, got {actual_fee} PLN"
                                                        else:
                                                            free_shipping_result = "✗ Could not verify fees"
                                                else:
                                                    free_shipping_result = "Not checked (missing data)"

                                                step_counter.print_step("Placing order")
                                                order_result = place_order()

                                                if order_result:
                                                    if isinstance(order_result, str):
                                                        print(f"✓ Order successfully placed! Order number: {order_result}")
                                                    else:
                                                        print("✓ Order successfully placed!")
                                                    print("Please check your email and 1C system for order confirmation")
                                                else:
                                                    print("✗ Failed to place order")
                                            else:
                                                print("✗ Failed to fill order form")
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
        print(f"Item price: {order_price if order_price else 'N/A'} PLN")
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

if __name__ == "__main__":
    main_pl()
