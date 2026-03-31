CHANGED:
!IMPORTANT! 
pip install -r requirements.txt (to get the need packages installed)
Don't forget makemigration and migrate.

Base.html - navbar now sticks to the top of the page. Changed text font for the navbar, 
hover tabs has an animation and changed the selected tab style. 
Added profile images to the account dropdown panel, and 
formated the success and Form submission errors(django backend validation) to be shown as a flash cards under the navbar

account.html - added a profile image wrapper to the account container. 

create_offer.html - 
Added an upload photos button with multi-image upload preview, main photo badge, 
corrected color css, and includes auth.js for frontend
live-input validation (title and city).

create_request.html - 
Made the style similar to offer, moved unhoused requests to dashboard. 
Current no image support, but can be changed later.
Has frontend live-input validation from auth.js (title, and city).

available_offers.html - 
now shows card listings that will open the modal when clicked.
Has default image based on their category.
Might move this to the dashboard later.

volunteer_requests.html - 
now shows card listings that will open the modal when clicked.
Has default image based on their category, in there is no image uploaded.
Might move this to the dashboard later.

register.html - changed the style to match more with the login, and has email verification. 

login.html - now forgot password works, with email verification.

MyApp/forms.py - 
Added a bunch more strict validation errors for both Register Form and the Profile Settings Form 
(Phone Number, Address, Name, Username, Role, Zip-code). Now Zip-code does validation against Zippopotam. 
Changed phonenumbers to be stored as digits only as it was stripping non-digits for validation, but returned original formattted string.
DJANGO'S BUILD-IN PASSWORD IS NOW ON! (sorry). There is an image upload validation.

MyApp/views.py - 
Added an email verification to the Register(View), 
which waits until the user enters a 6 digit activation code to set the user as active 
and have their account as registered.
Added a resend_verification code with a 30-second cooldown timer. 
Add an email verification to the LoginView, so that the user will get a message that they have to verify their email 
to be able to log in.
Changed create_request as open requests, processing requests, and completed requests were only defined inside for GET requests.
If the request is POST and the form is invalid, the code still goes to render() which caused issues.
So, now it covers GET request, POST + valid form, and POST + invalid form.
Now has status management (open/claimed/fulfilled/cancelled).
Now has messaging integration, pagination handling (Redirects + Return flow),
flash messages integration, and image handling. Improved safer data handling (user action safety checks).

messaging/views.py , /models, /forms - 
now are able to use messaging from anywhere on the website. 
Currently can use it in offers/requests/inbox.
one thread = one conversation, and there can be many messages in that thread. 
Able to handle multiple user in a thread, but not currently implemented.
Threads are ordered in recent activity. (WILL DO MORE WORK LATER)

unhoused_dash.html , volunteer_dash.html - 
Very basic implementation of where to manage their offers/requests. 
Might rework it by adding a tabs to see past, pending, and complete offers/requests (kinda like how settings now has it)
(NEEDS WORK!!!)

NEW:

auth.js - 
Has frontend verification for form fields. It validates email, name, city, listed item title, and listed item city. 
It also includes a ZIP Code auto-fill, character count for certain fields, a phone number format, a hidden password toggle, password matching validation. 
There are hook validation functions for live incorrect feedback. 
Lastly, this is now its own file, and not page specific, so you can add or include in future works. 

item_modal.js -
This file controls the reusable item modal used across item-card pages.
* opens the modal from a clicked card
* builds one normalized item object from the card’s `data-*` attributes
* stores modal state in `modalState`
* renders item details, images, and available actions
* switches between modal panels like:

  * detail
  * primary action
  * message
  * report
  * edit
  * delete
* restores modal state after redirects when needed 
(currently used to reload the page after msg/edit, but might delete or find different use)

How the file is organized:
* **Bootstrap**: startup logic when the page loads
* **DOM references**: cached modal elements
* **Modal state**: current item, images, active panel, etc.
* **Helpers**: small reusable utility functions
* **State access helpers**: read/write modal state
* **Storage helpers**: reopen/return/highlight state
* **Image helpers**: image rendering and navigation
* **Panel controller**: switches between modal panels
* **Normalization**: `buildCardData(card)` converts card `data-*` into one modal item object
* **Lifecycle**: open/close/populate modal
* **Submit handlers**: form validation before submit
* **Event binding**: attaches click and submit listeners

IMPORTANT
The modal should run from **one normalized item object** stored in modal state. So currently offers/requests are one object.
That means:
* if you add a new card field, update `buildCardData(card)`
* if you add a new modal panel, update the panel controller section
* if you add a new button/action, update the normalized `actions` logic and button rendering

If you need to edit something
* **Add a new item field** → update `buildCardData(card)` and the render logic
* **Add a new panel** → update panel DOM refs, panel controller functions, and restore logic
* **Add a new default image** → update `getDefaultCategoryImage()`
* **Change modal button visibility** → update normalized `actions` in `buildCardData(card)` and `configureActionButtons()`

Related files
* `item_modal.html` = modal markup
* `item_modal.css` = modal styling
* card templates like `available_offers.html` / `volunteer_requests.html` provide the `data-*` values the modal reads


Added:
Email verification (Register & settings) & Forgot Password:

On Login:
if email does not exist → “Invalid email or password.”
if email exists but inactive → set session and redirect to verify_email
on verify page → let them submit or resend code
after success → auto-login and redirect by role
for settings after success → login page

Current group email is HelpingConnections.team@gmail.com


