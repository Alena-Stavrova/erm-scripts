# lvh-scripts
Stack: Python, Selenium

These scripts automate order placement that is a part of our regression testing/system health check. They imitate a real user's behavior:
* go to the main page
* search for a particular item (chosen randomly from a list of SKUs, the list contains different price groups)
* add the item to cart
* fill order form
* select payment and/or delivery options randomly (whichever are available on a particular website). Sometimes includes interactive 3rd party elements (dropdowns, maps etc.)
* place an order
* print a helpful summary in the end (e.g. order number, item's price, cost of delivery etc.)
* similar to Levenhuk scripts, but the websites layout and design differ  

Scripts done: IT <img width="16" height="11" alt="image" src="https://raw.githubusercontent.com/stevenrskelton/flag-icon/master/png/16/country-4x3/it.png"> (1 / 8)

For each country, there will be 2 scripts:
* <ins>random</ins>: choose payment and/or delivery option randomly; used for daily smoke tests where we typically test 1 random flow
* <ins>choice</ins>: choose payment and/or delivery option that the user selects; can test any flow within possible payment/delivery combinations; used for montly system health check where we typically test all flows or all flows with 3rd-party systems

UPD March 16 '26: I actually have a full collection of ERM scripts but the code is messy and bloated. I'm cleaning them up using LVH scripts as a standard/template. I'm also writing a runner script so that several ERM scripts can be run automatically one after another. Both goals require editing and cleaning the existing scripts, and it's a slow process. Meanwhile, the versions posted here are:
* V0 = sloppy unedited version
* V1 = current working version (edited), but doesn't work with the runner yet
* V2 = edited version that a runner can run
