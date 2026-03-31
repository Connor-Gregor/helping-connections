// ============================================================
// AUTH + FORM VALIDATION BOOTSTRAP
// Handles:
// - account/register/settings validation
// - item (offer/request + modal edit) validation
// - password toggles
// - ZIP auto-fill
// ============================================================

document.addEventListener("DOMContentLoaded", function () {
    const isSettingsPage = !!document.querySelector('[data-settings-page="true"]');

// ============================================================
// VALIDATION RULES
// These functions define what is considered valid.
// Used by BOTH:
// - live validation (attach... functions)
// - modal submit validation (item_modal.js)
// ============================================================
    function isValidItemTitle(value, maxLength = 60) {
        const trimmed = (value || "").trim();
        return trimmed.length >= 3 && trimmed.length <= maxLength;
    }

    function isValidItemCity(value, maxLength = 25) {
        const trimmed = (value || "").trim();
        return trimmed.length >= 2 &&
            trimmed.length <= maxLength &&
            /^[A-Za-z\s'-]+$/.test(trimmed);
    }

// ============================================================
// SHARED UI HELPERS
// Responsible for:
// - applying valid/invalid styles
// - displaying inline error messages
// - updating character counters
// ============================================================

    function setValidityState(input, errorEl, message, isValid, showValid = true) {
        if (!input) return;

        input.classList.remove("input-error", "input-valid");

        if (errorEl) {
            errorEl.textContent = "";
        }

        if (!input.value.trim()) {
            return;
        }

        if (isValid) {
            if (showValid && document.activeElement === input) {
                input.classList.add("input-valid");
            }
        } else {
            input.classList.add("input-error");
            if (errorEl) {
                errorEl.textContent = message;
            }
        }
    }

    function updateCharCount(input, el, max = 30) {
        if (!input || !el) return;

        const length = input.value.length;
        el.textContent = `${length}/${max}`;

        if (length >= max) {
            el.style.color = "#e74c3c";
        } else if (length > max - 5) {
            el.style.color = "#f39c12";
        } else {
            el.style.color = "#64748b";
        }
    }

// ============================================================
// BASIC FIELD VALIDATORS
// Simple reusable checks for common field types
// ============================================================

    function isValidEmail(email) {
        const value = email.trim();
        if (!value) return false;

        const emailPattern = /^[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+\.)+[A-Za-z]{2,}$/;
        if (!emailPattern.test(value)) return false;

        const parts = value.split("@");
        if (parts.length !== 2) return false;

        const localPart = parts[0];
        const domainPart = parts[1];

        if (localPart.includes("..") || domainPart.includes("..")) return false;

        if (
            domainPart.startsWith(".") ||
            domainPart.endsWith(".") ||
            domainPart.startsWith("-") ||
            domainPart.endsWith("-")
        ) {
            return false;
        }

        const labels = domainPart.split(".");
        for (const label of labels) {
            if (!label) return false;
            if (label.startsWith("-") || label.endsWith("-")) return false;
            if (!/^[A-Za-z0-9-]+$/.test(label)) return false;
        }

        return true;
    }

    function isValidName(value) {
        return /^[A-Za-z .'-]+$/.test(value.trim());
    }

    function isValidCity(value) {
        return /^[A-Za-z .'-]+$/.test(value.trim());
    }

// ============================================================
// INPUT FORMATTERS
// Used to normalize user input (e.g., phone numbers)
// ============================================================

    function formatPhoneNumber(value) {
        let digits = value.replace(/\D/g, "").slice(0, 10);

        if (digits.length === 0) return "";

        if (digits.length < 4) {
            return digits;
        }

        if (digits.length < 7) {
            return `(${digits.slice(0, 3)}) ${digits.slice(3)}`;
        }

        return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
    }

// ============================================================
// FIELD VALIDATION ATTACHERS
// These connect validation logic to specific inputs
// using event listeners (input, blur)
// ============================================================

    function attachEmailValidation(inputId, errorId) {
        const input = document.getElementById(inputId);
        const errorEl = document.getElementById(errorId);
        if (!input) return;

        let touched = !isSettingsPage;

        function validate(showValid = touched) {
            const value = input.value.trim();

            if (!value) {
                input.classList.remove("input-error", "input-valid");
                if (errorEl) errorEl.textContent = "";
                return;
            }

            setValidityState(
                input,
                errorEl,
                "Please enter a valid email address.",
                isValidEmail(value),
                showValid
            );
        }

        validate(false);

        input.addEventListener("input", function () {
            touched = true;
            validate(true);
        });

        input.addEventListener("blur", function () {
            touched = true;
            validate(true);
        });
    }

    function attachNameValidation(inputId, errorId, countId, label, maxLength = 30) {
        const input = document.getElementById(inputId);
        const errorEl = document.getElementById(errorId);
        const countEl = countId ? document.getElementById(countId) : null;
        if (!input) return;

        let touched = !isSettingsPage;

        function validate(showValid = touched) {
            const value = input.value.trim();

            if (countEl) {
                updateCharCount(input, countEl, maxLength);
            }

            input.classList.remove("input-error", "input-valid");
            if (errorEl) errorEl.textContent = "";

            if (!value) {
                return;
            }

            if (value.length < 2) {
                setValidityState(input, errorEl, `${label} must be at least 2 characters.`, false);
                return;
            }

            if (value.length > maxLength) {
                setValidityState(input, errorEl, `${label} cannot exceed ${maxLength} characters.`, false);
                return;
            }

            if (!isValidName(value)) {
                setValidityState(
                    input,
                    errorEl,
                    `${label} can only contain letters, spaces, apostrophes, hyphens, and periods.`,
                    false
                );
                return;
            }

            setValidityState(input, errorEl, "", true, showValid);
        }

        validate(false);

        input.addEventListener("input", function () {
            touched = true;
            validate(true);
        });

        input.addEventListener("blur", function () {
            touched = true;
            validate(true);
        });
    }

    function attachPhoneValidation(inputId, errorId) {
        const input = document.getElementById(inputId);
        const errorEl = document.getElementById(errorId);
        if (!input) return;

        let touched = !isSettingsPage;

        function validate(showValid = touched) {
            const rawValue = input.value.trim();
            const digits = rawValue.replace(/\D/g, "");

            input.classList.remove("input-error", "input-valid");
            if (errorEl) errorEl.textContent = "";

            if (!rawValue) return;

            if (digits.length !== 10) {
                setValidityState(input, errorEl, "Enter a valid 10-digit phone number.", false);
                return;
            }

            setValidityState(input, errorEl, "", true, showValid);
        }

        function formatCurrentValue() {
            const currentValue = input.value || "";
            input.value = formatPhoneNumber(currentValue);
        }

        formatCurrentValue();
        validate(false);

        input.addEventListener("input", function () {
            touched = true;
            formatCurrentValue();
            validate(true);
        });

        input.addEventListener("blur", function () {
            touched = true;
            formatCurrentValue();
            validate(true);
        });
    }

    function isValidAddressLine1(value) {
        const trimmed = value.trim();

        if (trimmed.length < 5) return false;

        return /[A-Za-z0-9]/.test(trimmed);
    }

    function attachAddressLine1Validation(inputId, errorId) {
        const input = document.getElementById(inputId);
        const errorEl = document.getElementById(errorId);
        if (!input) return;

        let touched = !isSettingsPage;

        function normalizeSpaces() {
            input.value = input.value.replace(/\s{2,}/g, " ").trimStart();
        }

        function validate(showValid = touched) {
            const value = input.value.trim();

            input.classList.remove("input-error", "input-valid");
            if (errorEl) errorEl.textContent = "";

            if (!value) {
                return;
            }

            if (!isValidAddressLine1(value)) {
                setValidityState(
                    input,
                    errorEl,
                    "Enter a valid street address.",
                    false
                );
                return;
            }

            setValidityState(input, errorEl, "", true, showValid);
        }

        validate(false);

        input.addEventListener("input", function () {
            touched = true;
            normalizeSpaces();
            validate(true);
        });

        input.addEventListener("blur", function () {
            touched = true;
            normalizeSpaces();
            validate(true);
        });
    }

    function attachAddressLine2Cleanup(inputId) {
        const input = document.getElementById(inputId);
        if (!input) return;

        function normalize() {
            input.value = input.value.replace(/\s{2,}/g, " ").trimStart();
        }

        input.addEventListener("input", normalize);
        input.addEventListener("blur", normalize);
    }

    function attachCityValidation(inputId, errorId) {
        const input = document.getElementById(inputId);
        const errorEl = document.getElementById(errorId);
        if (!input) return;

        let touched = !isSettingsPage;

        function validate(showValid = touched) {
            const value = input.value.trim();

            input.classList.remove("input-error", "input-valid");
            if (errorEl) errorEl.textContent = "";

            if (!value) return;

            if (value.length < 2) {
                setValidityState(input, errorEl, "City must be at least 2 characters.", false);
                return;
            }

            if (!isValidCity(value)) {
                setValidityState(
                    input,
                    errorEl,
                    "City can only contain letters, spaces, apostrophes, hyphens, and periods.",
                    false
                );
                return;
            }

            setValidityState(input, errorEl, "", true, showValid);
        }

        validate(false);

        input.addEventListener("input", function () {
            touched = true;
            validate(true);
        });

        input.addEventListener("blur", function () {
            touched = true;
            validate(true);
        });

        input._validateCity = function () {
            validate(touched);
        };
    }

// ============================================================
// ITEM VALIDATION
// Shared between:
// - create item (offer/request forms)
// - modal edit panel
// ============================================================

    function attachItemTitleValidation(inputId, errorId, countId, maxLength = 60) {
        const input = document.getElementById(inputId);
        const errorEl = document.getElementById(errorId);
        const countEl = countId ? document.getElementById(countId) : null;
        if (!input) return;

        let touched = !isSettingsPage;

        function validate(showValid = touched) {
            if (input.value.length > maxLength) {
                input.value = input.value.slice(0, maxLength);
            }

            const value = input.value.trim();

            if (countEl) {
                updateCharCount(input, countEl, maxLength);
            }

            input.classList.remove("input-error", "input-valid");
            if (errorEl) errorEl.textContent = "";

            if (!value) {
                return;
            }

            if (!isValidItemTitle(value, maxLength)) {
                setValidityState(
                    input,
                    errorEl,
                    `Title must be between 3 and ${maxLength} characters.`,
                    false
                );
                return;
            }

            setValidityState(input, errorEl, "", true, showValid);
        }

        validate(false);

        input.addEventListener("input", function () {
            touched = true;
            validate(true);
        });

        input.addEventListener("blur", function () {
            touched = true;
            validate(true);
        });
    }

    function attachItemCityValidation(inputId, errorId, countId, maxLength = 25) {
        const input = document.getElementById(inputId);
        const errorEl = document.getElementById(errorId);
        const countEl = countId ? document.getElementById(countId) : null;
        if (!input) return;

        let touched = !isSettingsPage;

        function validate(showValid = touched) {
            if (input.value.length > maxLength) {
                input.value = input.value.slice(0, maxLength);
            }

            const value = input.value.trim();

            if (countEl) {
                updateCharCount(input, countEl, maxLength);
            }

            input.classList.remove("input-error", "input-valid");
            if (errorEl) errorEl.textContent = "";

            if (!value) {
                return;
            }

            if (!isValidItemCity(value, maxLength)) {
                setValidityState(
                    input,
                    errorEl,
                    "City must be 2–25 characters and only contain letters, spaces, apostrophes, hyphens, or periods.",
                    false
                );
                return;
            }

            setValidityState(input, errorEl, "", true, showValid);
        }

        validate(false);

        input.addEventListener("input", function () {
            touched = true;
            validate(true);
        });

        input.addEventListener("blur", function () {
            touched = true;
            validate(true);
        });
    }

// ============================================================
// PASSWORD + ADVANCED FORM HELPERS
// ============================================================

    function attachPasswordMatchValidation(password1Id, password2Id, error1Id, error2Id) {
        const password1 = document.getElementById(password1Id);
        const password2 = document.getElementById(password2Id);
        const error1 = document.getElementById(error1Id);
        const error2 = document.getElementById(error2Id);

        if (!password1 || !password2) return;

        let touched = !isSettingsPage;

        function validate(showValid = touched) {
            const value1 = password1.value;
            const value2 = password2.value;

            password1.classList.remove("input-error", "input-valid");
            password2.classList.remove("input-error", "input-valid");

            if (error1) error1.textContent = "";
            if (error2) error2.textContent = "";

            if (!value1 && !value2) return;

            if (value1 && showValid) {
                password1.classList.add("input-valid");
            }

            if (!value2) return;

            if (value1 !== value2) {
                password2.classList.add("input-error");
                if (error2) error2.textContent = "Passwords do not match.";
            } else if (showValid) {
                password2.classList.add("input-valid");
            }
        }

        validate(false);

        password1.addEventListener("input", function () {
            touched = true;
            validate(true);
        });

        password2.addEventListener("input", function () {
            touched = true;
            validate(true);
        });

        password1.addEventListener("blur", function () {
            touched = true;
            validate(true);
        });

        password2.addEventListener("blur", function () {
            touched = true;
            validate(true);
        });
    }

    function attachPasswordGroupToggle(wrapperSelector) {
        const wrappers = document.querySelectorAll(wrapperSelector);
        if (!wrappers.length) return;

        const buttons = document.querySelectorAll(`${wrapperSelector} .toggle-password`);

        // Prevent duplicate listeners when initializeAuthValidation()
        // runs more than once (like on settings tab switches)
        buttons.forEach(button => {
            if (button.dataset.toggleBound === "true") return;
            button.dataset.toggleBound = "true";

            button.addEventListener("click", function () {
                // Look at the first input in this group to determine current state
                const firstWrapper = wrappers[0];
                const firstInput = firstWrapper ? firstWrapper.querySelector("input") : null;
                if (!firstInput) return;

                const currentlyHidden = firstInput.type === "password";
                const newType = currentlyHidden ? "text" : "password";

                // Toggle every input in this group together
                wrappers.forEach(wrapper => {
                    const input = wrapper.querySelector("input");
                    const icon = wrapper.querySelector(".toggle-password i");
                    const buttonInWrapper = wrapper.querySelector(".toggle-password");

                    if (input) {
                        input.type = newType;
                    }

                    if (icon) {
                        icon.classList.toggle("fa-eye", currentlyHidden);
                        icon.classList.toggle("fa-eye-slash", !currentlyHidden);
                    }

                    if (buttonInWrapper) {
                        buttonInWrapper.setAttribute(
                            "aria-label",
                            currentlyHidden ? "Hide password" : "Show password"
                        );
                    }
                });
            });
        });
    }

// ============================================================
// ZIP LOOKUP (AUTO-FILL)
// Fetches city/state from ZIP and updates fields
// ============================================================

    function attachZipLookup(zipId, stateId, cityId, messageId) {
        const zipInput = document.getElementById(zipId);
        const stateSelect = document.getElementById(stateId);
        const cityInput = document.getElementById(cityId);
        const messageEl = document.getElementById(messageId);

        if (!zipInput || !stateSelect || !messageEl) return;

        let lastLookedUpZip = "";
        let lookupTimer = null;

        function resetZipFeedback() {
            zipInput.classList.remove("input-error", "input-valid");
            stateSelect.classList.remove("input-error", "input-valid");

            if (cityInput) {
                cityInput.classList.remove("input-error", "input-valid");
            }

            if (messageEl) {
                messageEl.textContent = "";
                messageEl.style.color = "#e74c3c";
            }
        }

        async function lookup() {
            const rawZip = zipInput.value.trim();
            const zip = rawZip.slice(0, 5);

            resetZipFeedback();

            if (!zip) {
                lastLookedUpZip = "";
                stateSelect.value = "";
                if (cityInput) cityInput.value = "";
                return;
            }

            if (!/^\d{5}$/.test(zip)) {
                zipInput.classList.add("input-error");
                messageEl.textContent = "Please enter a valid 5-digit U.S. ZIP code.";
                lastLookedUpZip = "";
                stateSelect.value = "";
                if (cityInput) cityInput.value = "";
                return;
            }

            if (zip === lastLookedUpZip) {
                return;
            }

            try {
                const response = await fetch(`https://api.zippopotam.us/us/${zip}`);
                if (!response.ok) throw new Error("ZIP not found");

                const data = await response.json();

                const places = Array.isArray(data.places) ? data.places : [];
                const place = places[0];

                if (!place) {
                    throw new Error("No location data found");
                }

                const stateAbbr = place["state abbreviation"];
                const cityName = place["place name"];

                stateSelect.value = stateAbbr;

                if (cityInput) {
                    cityInput.value = cityName;

                    if (typeof cityInput._validateCity === "function") {
                        cityInput._validateCity();
                    } else {
                        cityInput.classList.remove("input-error");
                        if (!isSettingsPage) {
                            cityInput.classList.add("input-valid");
                        }
                    }
                }

                if (!isSettingsPage) {
                    stateSelect.classList.add("input-valid");
                    zipInput.classList.add("input-valid");
                }

                messageEl.textContent = "State auto-selected and city filled.";
                messageEl.style.color = "#1abc9c";
                lastLookedUpZip = zip;
            } catch (error) {
                zipInput.classList.add("input-error");
                stateSelect.value = "";

                if (cityInput) {
                    cityInput.value = "";
                    cityInput.classList.remove("input-valid");
                }

                messageEl.textContent = "That ZIP code was not found. Please enter a real U.S. ZIP code.";
                messageEl.style.color = "#e74c3c";
                lastLookedUpZip = "";
            }
        }

        zipInput.addEventListener("input", function () {
            if (lookupTimer) {
                clearTimeout(lookupTimer);
            }

            const digitsOnly = zipInput.value.replace(/\D/g, "").slice(0, 5);
            zipInput.value = digitsOnly;

            lastLookedUpZip = "";
            resetZipFeedback();

            if (digitsOnly.length < 5) {
                stateSelect.value = "";
                if (cityInput) cityInput.value = "";
                return;
            }

            lookupTimer = setTimeout(() => {
                void lookup();
            }, 250);
        });

        zipInput.addEventListener("blur", function () {
            if (lookupTimer) {
                clearTimeout(lookupTimer);
            }

            void lookup();
        });
    }

// ============================================================
// INITIALIZER
// Wires all validation to the correct inputs on the page
// ============================================================

    function initializeAuthValidation() {
        attachEmailValidation("id_email", "email-live-error");
        attachNameValidation("id_first_name", "first-name-live-error", "first-name-count", "First name");
        attachNameValidation("id_last_name", "last-name-live-error", "last-name-count", "Last name");
        attachCityValidation("id_city", "city-live-error");
        attachPhoneValidation("id_phone_number", "phone-live-error");
        attachAddressLine1Validation("id_address_line1", "address1-live-error");
        attachAddressLine2Cleanup("id_address_line2");
        attachPasswordMatchValidation("id_password1", "id_password2", "password1-live-error", "password2-live-error");
        attachPasswordGroupToggle(".register-password-group");
        attachZipLookup("id_zip_code", "id_state", "id_city", "zip-live-message");

        attachEmailValidation("settings-email", "email-live-error");
        attachNameValidation("settings-first-name", "first-name-live-error", "first-name-count", "First name");
        attachNameValidation("settings-last-name", "last-name-live-error", "last-name-count", "Last name");
        attachCityValidation("settings-city", "city-live-error");
        attachPhoneValidation("settings-phone", "phone-live-error");
        attachAddressLine1Validation("settings-address-line1", "address1-live-error");
        attachAddressLine2Cleanup("settings-address-line2");
        attachPasswordMatchValidation("settings-new-password1", "settings-new-password2", "password1-live-error", "password2-live-error");
        attachPasswordGroupToggle(".settings-password-group");
        attachZipLookup("settings-zip", "settings-state", "settings-city", "zip-live-message");

        attachPasswordGroupToggle(".reset-password-group");
        attachPasswordMatchValidation("id_new_password1", "id_new_password2", "reset-password1-live-error", "reset-password2-live-error");

        attachItemTitleValidation("offer-title", "offer-title-live-error", "offer-title-count", 60);
        attachItemCityValidation("offer-city", "offer-city-live-error", "offer-city-count", 25);

        attachItemTitleValidation("id_title", "request-title-live-error", "request-title-count", 60);
        attachItemCityValidation("id_city", "request-city-live-error", "request-city-count", 25);

        attachItemTitleValidation("itemEditTitle", "itemEditTitleError", "itemEditTitleCount", 60);
        attachItemCityValidation("itemEditCity", "itemEditCityError", "itemEditCityCount", 25);
    }

// ============================================================
// PUBLIC EXPORTS (USED BY OTHER FILES)
// ============================================================

    initializeAuthValidation();
    window.initializeAuthValidation = initializeAuthValidation;
    window.isValidItemTitle = isValidItemTitle;
    window.isValidItemCity = isValidItemCity;
});