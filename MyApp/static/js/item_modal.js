document.addEventListener("DOMContentLoaded", function () {
    // ============================================================
    // ITEM MODAL BOOTSTRAP
    // This file controls the reusable item modal for offer/request cards.
    //
    // Main responsibilities:
    // - restore saved modal/page state after redirects
    // - collect modal DOM elements
    // - store modal state in one place
    // - render item details, images, and action panels
    // - handle message/report/edit/delete/claim-related flows
    //
    // modalState is the source for the modal.
    // ============================================================

    // ------------------------------------------------------------
    const savedScroll = sessionStorage.getItem("itemModalScrollY");
    const returnItemId = sessionStorage.getItem("itemModalReturnItemId");

    if (savedScroll) {
        window.scrollTo(0, parseInt(savedScroll, 10));
        sessionStorage.removeItem("itemModalScrollY");
    }

    if (returnItemId) {
        const card = findCardByItemId(returnItemId);

        if (card) {
            card.classList.add("item-card-returned");

            setTimeout(() => {
                card.classList.remove("item-card-returned");
            }, 2000);
        }

        clearReturnItemState();
    }

    // ------------------------------------------------------------
    // Find the cards that can open this modal and the modal shell.
    // Exit early on pages that do not use this reusable modal.
    // ------------------------------------------------------------
    const cards = document.querySelectorAll(".js-item-card");
    const modal = document.getElementById("itemPreviewModal");

    if (!modal || !cards.length) return;


    // ============================================================
    // DOM REFERENCES
    // Cache all modal-related DOM elements once at startup.
    // This keeps the rest of the controller focused on behavior
    // instead of repeated document queries.
    // ============================================================
    // Modal shell controls
    const closeBtn = document.getElementById("itemModalClose");
    const prevBtn = document.getElementById("itemModalPrev");
    const nextBtn = document.getElementById("itemModalNext");

    // Main detail display
    const modalImage = document.getElementById("itemModalImage");
    const modalEmpty = document.getElementById("itemModalEmpty");
    const modalThumbs = document.getElementById("itemModalThumbs");

    // Detail content fields
    const modalTitle = document.getElementById("itemModalTitle");
    const modalOwnerPhoto = document.getElementById("itemModalOwnerPhoto");
    const modalOwnerInitials = document.getElementById("itemModalOwnerInitials");
    const modalOwnerName = document.getElementById("itemModalOwnerName");
    const modalOwnerTime = document.getElementById("itemModalOwnerTime");
    const modalCategory = document.getElementById("itemModalCategory");
    const modalCity = document.getElementById("itemModalCity");
    const modalLocation = document.getElementById("itemModalLocation");
    const modalStatus = document.getElementById("itemModalStatus");
    const modalDescription = document.getElementById("itemModalDescription");
    const modalClaimedAtRow = document.getElementById("itemModalClaimedAtRow");
    const modalClaimedAt = document.getElementById("itemModalClaimedAt");

    // Modal panels
    const detailPanel = document.getElementById("itemDetailPanel");
    const primaryPanel = document.getElementById("itemPrimaryPanel");
    const messagePanel = document.getElementById("itemMessagePanel");
    const reportPanel = document.getElementById("itemReportPanel");
    const editPanel = document.getElementById("itemEditPanel");
    const deletePanel = document.getElementById("itemDeletePanel");

    // Footer action buttons
    const primaryBtn = document.getElementById("itemModalPrimaryBtn");
    const messageBtn = document.getElementById("itemModalMessageBtn");
    const reportBtn = document.getElementById("itemModalReportBtn");
    const editBtn = document.getElementById("itemModalEditBtn");
    const deleteBtn = document.getElementById("itemModalDeleteBtn");
    const messageClaimerBtn = document.getElementById("itemModalMessageClaimerBtn");
    const verifyBtn = document.getElementById("itemModalVerifyBtn");
    const hideBtn = document.getElementById("itemModalHideBtn");

    // Primary action panel
    const primaryTitle = document.getElementById("itemPrimaryTitle");
    const primaryForm = document.getElementById("itemPrimaryForm");
    const primaryBackBtn = document.getElementById("itemPrimaryBackBtn");
    const primaryPanelTitle = document.getElementById("itemPrimaryPanelTitle");
    const primaryNote = document.getElementById("itemPrimaryNote");
    const primaryConfirmBtn = document.getElementById("itemPrimaryConfirmBtn");
    const primaryItemId = document.getElementById("itemPrimaryItemId");
    const primaryReturnPageNumber = document.getElementById("itemPrimaryReturnPageNumber");
    const primaryReturnQuery = document.getElementById("itemPrimaryReturnQuery");

    // Message panel
    const messageUserName = document.getElementById("itemMessageUserName");
    const messageItemTitle = document.getElementById("itemMessageTitle");
    const messageRecipientId = document.getElementById("itemMessageRecipientId");
    const messageBody = document.getElementById("itemMessageBody");
    const messageBackBtn = document.getElementById("itemMessageBackBtn");
    const messageForm = document.getElementById("itemMessageForm");
    const messageReturnQuery = document.getElementById("itemMessageReturnQuery");
    const messageReturnTo = document.getElementById("itemMessageReturnTo");
    const messageReturnItemId = document.getElementById("itemMessageReturnItemId");
    const messageReturnPage = document.getElementById("itemMessageReturnPage");
    const messageReturnPageNumber = document.getElementById("itemMessageReturnPageNumber");
    const messageError = document.getElementById("itemMessageError");

    // Report panel
    const reportHeading = document.getElementById("itemReportHeading");
    const reportOfferId = document.getElementById("itemReportOfferId");
    const reportRequestId = document.getElementById("itemReportRequestId");
    const reportUserName = document.getElementById("itemReportUserName");
    const reportItemTitle = document.getElementById("itemReportTitle");
    const reportUserId = document.getElementById("itemReportUserId");
    const reportReason = document.getElementById("itemReportReason");
    const reportDetails = document.getElementById("itemReportDetails");
    const reportBackBtn = document.getElementById("itemReportBackBtn");
    const reportForm = document.getElementById("itemReportForm");
    const reportError = document.getElementById("itemReportError");
    const reportReturnTo = document.getElementById("itemReportReturnTo");

    // Edit panel
    const editPanelTitle = document.getElementById("itemEditPanelTitle");
    const editReturnPageNumber = document.getElementById("itemEditReturnPageNumber");
    const editForm = document.getElementById("itemEditForm");
    const editTitle = document.getElementById("itemEditTitle");
    const editCategory = document.getElementById("itemEditCategory");
    const editCity = document.getElementById("itemEditCity");
    const editLocation = document.getElementById("itemEditLocation");
    const editDescription = document.getElementById("itemEditDescription");
    const editBackBtn = document.getElementById("itemEditBackBtn");

    const modalEmailRow = document.getElementById("itemModalEmailRow");
    const modalEmail = document.getElementById("itemModalEmail");
    const modalPhoneRow = document.getElementById("itemModalPhoneRow");
    const modalPhone = document.getElementById("itemModalPhone");
    const modalRoleRow = document.getElementById("itemModalRoleRow");
    const modalRole = document.getElementById("itemModalRole");

    const adminEditFields = document.getElementById("itemAdminEditFields");
    const standardEditFields = document.getElementById("itemStandardEditFields");

    const editDisplayUsername = document.getElementById("itemEditDisplayUsername");
    const editFirstName = document.getElementById("itemEditFirstName");
    const editLastName = document.getElementById("itemEditLastName");
    const editEmail = document.getElementById("itemEditEmail");
    const editPhone = document.getElementById("itemEditPhone");
    const editAdminCity = document.getElementById("itemEditAdminCity");
    const editState = document.getElementById("itemEditState");
    const editRole = document.getElementById("itemEditRole");
    const editReturnQuery = document.getElementById("itemEditReturnQuery");
    const editReturnItemId = document.getElementById("itemEditReturnItemId");

    // Delete panel
    const deleteForm = document.getElementById("itemDeleteForm");
    const deleteTitle = document.getElementById("itemDeleteTitle");
    const deleteBackBtn = document.getElementById("itemDeleteBackBtn");
    const deleteReturnQuery = document.getElementById("itemDeleteReturnQuery");

    // Admin viewing account stuff
    const itemAccountInfo = document.getElementById("itemAccountInfo");
    const itemAccountUsername = document.getElementById("itemAccountUsername");
    const itemAccountFirstName = document.getElementById("itemAccountFirstName");
    const itemAccountLastName = document.getElementById("itemAccountLastName");
    const itemAccountEmail = document.getElementById("itemAccountEmail");
    const itemAccountPhone = document.getElementById("itemAccountPhone");
    const itemAccountCity = document.getElementById("itemAccountCity");
    const itemAccountState = document.getElementById("itemAccountState");
    const itemAccountRole = document.getElementById("itemAccountRole");
    const itemAccountJoined = document.getElementById("itemAccountJoined");

    const itemStandardUserBlock = document.getElementById("itemStandardUserBlock");
    const itemStandardMetaBlock = document.getElementById("itemStandardMetaBlock");
    const itemStandardDescriptionBlock = document.getElementById("itemStandardDescriptionBlock");
    const itemModalLeft = document.getElementById("itemModalLeft");

    // ============================================================
    // MODAL STATE
    //
    // Stores:
    // - current normalized item
    // - current image list and active image index
    // - pending processing action (if any)
    // - currently active panel
    // - extra context for panel-specific behavior
    //
    // If new modal state is needed later, add it here first.
    // ============================================================
    const modalState = {
        item: null,
        images: [],
        imageIndex: 0,
        pendingProcessingAction: null,
        activePanel: "detail",
        panelContext: null,
    };

    // ============================================================
    // GENERIC HELPERS
    // Small reusable helpers for DOM visibility, parsing, formatting,
    // and simple utility behavior used across the controller.
    // ============================================================

    // Show an element using the provided display mode.
    function showElement(element, displayValue = "block") {
        if (!element) return;
        element.style.display = displayValue;
    }

    // Hide an element without removing it from the DOM.
    function hideElement(element) {
        if (!element) return;
        element.style.display = "none";
    }

    // Delays focus until after the panel has rendered visibly.
    function focusFieldLater(field) {
        if (!field) return;

        setTimeout(() => {
            field.focus();
        }, 0);
    }

    // Safely parse a card's image JSON into an array of image URLs.
    function parseImages(imagesValue) {
        if (!imagesValue) return [];

        try {
            const parsed = JSON.parse(imagesValue);
            return Array.isArray(parsed) ? parsed.filter(Boolean) : [];
        } catch (error) {
            console.warn("Could not parse item images JSON:", error);
            return [];
        }
    }

    // Fallback image map used when an item has no uploaded images.
    // Edit this if you add new categories or default category images.
    function getDefaultCategoryImage(categoryValue, categoryLabel) {
        const rawCategory = (categoryValue || categoryLabel || "").trim().toLowerCase();

        const categoryMap = {
            "food": "/static/images/food.jpg",
            "clothing": "/static/images/clothes.jpg",
            "blankets": "/static/images/blanket.jpg",
            "blankets / bedding": "/static/images/blanket.jpg",
            "hygiene": "/static/images/hygiene.jpg",
            "hygiene items": "/static/images/hygiene.jpg",
            "transport": "/static/images/transportation.jpg",
            "transportation": "/static/images/transportation.jpg",
            "medical": "/static/images/medical.jpg",
            "medical supplies": "/static/images/medical.jpg"
        };

        return categoryMap[rawCategory] || "/static/images/food.jpg";
    }

    // Returns extra context for the currently active panel.
    function getPanelContext() {
        return modalState.panelContext || null;
    }

    function getCurrentReturnQuery() {
        const query = window.location.search || "";
        return query.startsWith("?") ? query.slice(1) : query;
    }

    // Reads the current pagination page from the URL query string.
    function getCurrentPageNumber() {
        const params = new URLSearchParams(window.location.search);
        return params.get("page") || "1";
    }

    // Detects which page/view the modal is being used from.
    // Used to preserve return navigation and redirect behavior.
    function getCurrentPage() {
        const path = window.location.pathname || "";

        if (path.includes("/offers/mine/")) return "my_offers";
        if (path.includes("/offers/")) return "available_offers";
        if (path.includes("/requests/") && !path.includes("/create/")) return "volunteer_requests";
        if (path.includes("/unhoused_dash/")) return "unhoused";
        if (path.includes("/volunteer/")) return "volunteer";
        return "";
    }

    // Formats backend date values for display inside the modal.
    function formatPostedDate(value) {
        if (!value) return "";
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return value;

        return date.toLocaleString([], {
            month: "short",
            day: "numeric",
            year: "numeric",
            hour: "numeric",
            minute: "2-digit"
        });
    }

    // Hides every modal panel before showing the next active one.
    function hideAllPanels() {
        hideElement(detailPanel);
        hideElement(primaryPanel);
        hideElement(messagePanel);
        hideElement(reportPanel);
        hideElement(editPanel);
        hideElement(deletePanel);
    }

    // Clears image thumbnail markup before rebuilding it.
    function clearThumbs() {
        if (modalThumbs) modalThumbs.innerHTML = "";
    }

    // Resets shared panel validation/error messages.
    function clearPanelErrors() {
        if (messageError) {
            messageError.textContent = "Please enter a message before sending.";
            hideElement(messageError);
        }

        if (reportError) {
            reportError.textContent = "Please choose a reason.";
            hideElement(reportError);
        }
    }

    // Clears report form fields and restores default report error state.
    function resetReportPanelState() {
        if (reportOfferId) {
            reportOfferId.value = "";
        }

        if (reportRequestId) {
            reportRequestId.value = "";
        }

        if (reportReason) {
            reportReason.value = "";
        }

        if (reportDetails) {
            reportDetails.value = "";
        }

        if (reportError) {
            reportError.textContent = "Please choose a reason.";
            hideElement(reportError);
        }
    }

    // Clears message form fields and restores default message error state.
    function resetMessagePanelState() {
        if (messageError) {
            messageError.textContent = "Please enter a message before sending.";
            hideElement(messageError);
        }

        if (messageBody) {
            messageBody.value = "";
        }
    }

    // ============================================================
    // STATE ACCESS HELPERS
    // These helpers read and write modalState so the rest of the file
    // can stay readable and consistent.
    // ============================================================

    // Direct accessor for the current modal item in state.
    function getStateItem() {
        return modalState.item;
    }

    // Use this in helper-style functions when "current item" reads more clearly
    // than directly referencing modalState.item.
    function getCurrentItem() {
        return getStateItem();
    }

    // Returns the current pending processing action, if one is set.
    function getPendingProcessingAction() {
        return modalState.pendingProcessingAction || null;
    }

    // Returns the active image list for the modal.
    function getCurrentImages() {
        return Array.isArray(modalState.images)
            ? modalState.images
            : [];
    }

    // Returns the currently selected image index.
    function getCurrentImageIndex() {
        return typeof modalState.imageIndex === "number"
            ? modalState.imageIndex
            : 0;
    }

    // Returns the normalized owner object for the active item.
    function getCurrentOwner() {
        const stateItem = getStateItem();

        if (stateItem && stateItem.owner) {
            return stateItem.owner;
        }

        return getCurrentItem()?.owner || null;
    }

    // Returns the normalized status object for the active item.
    function getCurrentStatus() {
        const stateItem = getStateItem();

        if (stateItem && stateItem.status) {
            return stateItem.status;
        }

        return getCurrentItem()?.status || null;
    }

    // Returns the normalized claim/claimer info for the active item.
    function getCurrentClaim() {
        const stateItem = getStateItem();

        if (stateItem && stateItem.claim) {
            return stateItem.claim;
        }

        return getCurrentItem()?.claim || null;
    }

    // Finds a matching card in the DOM by item id across known card variants.
    function findCardByItemId(itemId) {
        if (!itemId) return null;

        return (
            document.getElementById(`item-card-${itemId}`) ||
            document.getElementById(`item-card-open-${itemId}`) ||
            document.getElementById(`item-card-available-${itemId}`) ||
            document.getElementById(`item-card-processing-${itemId}`) ||
            document.getElementById(`item-card-completed-${itemId}`)
        );
    }

    // True when the active modal item is request-based instead of offer-based.
    function isCurrentItemRequest() {
        return (modalState.item?.actionMode || "").startsWith("request");
    }

    // Builds the correct message target using the active item
    // and current panel context (owner vs claimer).
    function getCurrentMessageTarget() {
        const item = getCurrentItem();
        const owner = getCurrentOwner();
        const claim = getCurrentClaim();
        const context = getPanelContext();

        if (!item) return null;

        if (context?.targetType === "claimer" && claim?.claimerId) {
            return {
                type: "claimer",
                id: claim.claimerId,
                name: claim.claimedBy || "Claimer",
                returnTo: getCurrentPage() || "my_offers"
            };
        }

        if (owner?.id) {
            if (String(owner.id) === String(item?.currentUserId || "")) {
                return null;
            }

            return {
                type: "owner",
                id: owner.id,
                name: owner.name || "",
                returnTo: getCurrentPage() || "available_offers"
            };
        }

        return null;
    }

    // Builds the correct report target and endpoint for the active item.
    function getCurrentReportTarget() {
        const item = getCurrentItem();
        const owner = getCurrentOwner();

        if (!item) return null;

        const isRequest = isCurrentItemRequest();

        return {
            type: isRequest ? "request_report" : "offer_report",
            itemId: item.itemId || "",
            ownerId: owner?.reportId || owner?.id || "",
            ownerName: owner?.name || "",
            action: isRequest ? "/reports/requests/create/" : "/offers/report/",
            heading: isRequest ? "Report Request" : "Report Offer"
        };
    }

    // Returns the main action button label for the active item.
    function getCurrentPrimaryLabel() {
        const stateItem = getStateItem();

        if (stateItem && typeof stateItem.primaryLabel === "string" && stateItem.primaryLabel.length) {
            return stateItem.primaryLabel;
        }

        return getCurrentItem()?.primaryLabel || "Claim Offer";
    }

    // Returns the normalized action URLs for the active item.
    function getCurrentUrls() {
        const stateItem = getStateItem();

        if (stateItem && stateItem.urls) {
            return stateItem.urls;
        }

        return getCurrentItem()?.urls || {};
    }

    // Returns the normalized action visibility/permission flags.
    function getCurrentActions() {
        const stateItem = getStateItem();

        if (stateItem && stateItem.actions) {
            return stateItem.actions;
        }

        return getCurrentItem()?.actions || {};
    }

    // Stores the panel currently being shown in the modal.
    function setActivePanel(panelName) {
        modalState.activePanel = panelName || "detail";
    }

    // Stores extra context needed by panel-specific workflows.
    function setPanelContext(context) {
        modalState.panelContext = context || null;
    }

    // Clears panel-specific context when returning to neutral modal state.
    function clearPanelContext() {
        modalState.panelContext = null;
    }

    // Sets the active normalized item in modal state.
    function setCurrentItem(item) {
        modalState.item = item;
    }

    // Replaces the active modal image list.
    function setCurrentImages(images) {
        modalState.images = Array.isArray(images) ? images : [];
    }

    // Sets which image in the current image list is selected.
    function setCurrentImageIndex(index) {
        modalState.imageIndex = typeof index === "number" ? index : 0;
    }

    // Stores the temporary processing action for confirm-style flows.
    function setPendingProcessingAction(action) {
        modalState.pendingProcessingAction =
            typeof action === "string" && action.length
                ? action
                : null;
    }

    // Replaces the image list and resets the image index back to the first image.
    function resetImageState(images) {
        setCurrentImages(images);
        setCurrentImageIndex(0);
    }

    // ============================================================
    // PAGE / STORAGE STATE HELPERS
    // These helpers return highlighting,
    // hidden dashboard items, and scroll restoration across navigation.
    // ============================================================

    // Resets modal state back to its default neutral values.
    function resetModalState() {
        setCurrentItem(null);
        setCurrentImages([]);
        setCurrentImageIndex(0);
        setPendingProcessingAction(null);
        setActivePanel("detail");
        clearPanelContext();
    }

    // Reads locally hidden completed request ids from localStorage.
    function getHiddenDashboardRequests() {
        try {
            return JSON.parse(localStorage.getItem("hiddenDashboardRequests") || "[]");
        } catch (e) {
            return [];
        }
    }

    // Persists hidden completed request ids in localStorage.
    function saveHiddenDashboardRequests(ids) {
        localStorage.setItem("hiddenDashboardRequests", JSON.stringify(ids));
    }

    // Saves which item should be visually highlighted after returning.
    function saveReturnItemState(itemId) {
        sessionStorage.setItem("itemModalReturnItemId", itemId || "");
    }

    // Clears the saved returned-item highlight state.
    function clearReturnItemState() {
        sessionStorage.removeItem("itemModalReturnItemId");
    }


    // ============================================================
    // IMAGE RENDERING / NAVIGATION
    // Handles the main modal image, empty-state fallback, arrows,
    // thumbnail rendering, and image switching.
    // ============================================================

    // Renders the current image state into the modal image area.
    function updateImageView() {
        const images = getCurrentImages();
        const imageIndex = getCurrentImageIndex();

        clearThumbs();

        if (!hasImages()) {
            hideElement(modalImage);
            showElement(modalEmpty, "block");
            hideElement(prevBtn);
            hideElement(nextBtn);
            return;
        }

        hideElement(modalEmpty);
        showElement(modalImage, "block");
        modalImage.src = images[imageIndex];

        if (images.length > 1) {
            showElement(prevBtn, "flex");
            showElement(nextBtn, "flex");
        } else {
            hideElement(prevBtn);
            hideElement(nextBtn);
        }

        images.forEach((src, index) => {
            const thumb = document.createElement("img");
            thumb.src = src;
            thumb.alt = "Preview image";
            thumb.className = "item-modal-thumb";

            if (index === imageIndex) {
                thumb.classList.add("active");
            }

            thumb.addEventListener("click", function (e) {
                e.stopPropagation();
                setCurrentImageIndex(index);
                updateImageView();
            });

            if (modalThumbs) {
                modalThumbs.appendChild(thumb);
            }
        });
    }

    // Moves to the previous image, wrapping around if needed.
    function showPreviousImage() {
        const images = getCurrentImages();
        if (!hasImages()) return;

        const nextIndex = (getCurrentImageIndex() - 1 + images.length) % images.length;

        setCurrentImageIndex(nextIndex);
        updateImageView();
    }

    // True when the modal has at least one image to display.
    function hasImages() {
        return getCurrentImages().length > 0;
    }

    // True when image navigation controls should be available.
    function hasMultipleImages() {
        return getCurrentImages().length > 1;
    }

    // Moves to the next image, wrapping around if needed.
    function showNextImage() {
        const images = getCurrentImages();
        if (!hasImages()) return;

        const nextIndex = (getCurrentImageIndex() + 1) % images.length;

        setCurrentImageIndex(nextIndex);
        updateImageView();
    }


    // ============================================================
    // PANEL CONTROLLER
    // These functions switch the modal between panels and populate
    // panel-specific content using the active modal item/state.
    // Edit here if you add a new panel workflow later.
    // ============================================================

    // Shared panel switch helper used by all panel-specific show functions.
    function openPanel(panelElement, panelName, options = {}) {
        const {
            clearContext = false,
            resetPendingAction = false,
            display = "flex"
        } = options;

        if (resetPendingAction) {
            setPendingProcessingAction(null);
        }

        if (clearContext) {
            clearPanelContext();
        }

        setActivePanel(panelName);
        hideAllPanels();
        showElement(panelElement, display);
        clearPanelErrors();
    }

    // Shows the default item detail panel.
    function showDetailPanel() {
        if (primaryConfirmBtn) {
            primaryConfirmBtn.classList.remove("item-danger-btn");
        }
        openPanel(detailPanel, "detail", {
            clearContext: true,
            resetPendingAction: true
        });
    }

    // Shows the primary action panel for the current item.
    function showPrimaryPanel() {
        const item = modalState.item;
        if (!item) return;

        openPanel(primaryPanel, "primary", {
            clearContext: true,
            resetPendingAction: true
        });

        if (primaryPanelTitle) {
            primaryPanelTitle.textContent = item.primaryPanelTitle || "Confirm this action?";
        }

        if (primaryTitle) {
            primaryTitle.textContent = item.title || "";
        }

        if (primaryNote) {
            primaryNote.textContent = item.primaryNote || "";
        }

        if (primaryItemId) {
            primaryItemId.value = item.itemId || "";
        }

        if (primaryReturnPageNumber) {
            primaryReturnPageNumber.value = getCurrentPageNumber();
        }

        if (primaryReturnQuery) {
            primaryReturnQuery.value = getCurrentReturnQuery();
        }

        if (primaryConfirmBtn) {
            primaryConfirmBtn.textContent = item.primaryConfirmLabel || item.primaryLabel || "Confirm";
        }

        const urls = getCurrentUrls();
        if (primaryForm) {
            primaryForm.action = urls.primary || "";
        }
    }

    // Shows the special confirm panel for request-processing edit/delete flows.
    function showProcessingRequestConfirm(actionType) {
        const item = modalState.item;
        if (!item) return;

        setPendingProcessingAction(actionType);

        openPanel(primaryPanel, "primary", {
            clearContext: true
        });

        if (primaryTitle) {
            primaryTitle.textContent = item.title || "";
        }

        if (primaryItemId) {
            primaryItemId.value = item.itemId || "";
        }

        if (primaryReturnPageNumber) {
            primaryReturnPageNumber.value = getCurrentPageNumber();
        }

        if (primaryReturnQuery) {
            primaryReturnQuery.value = getCurrentReturnQuery();
        }

        if (primaryPanelTitle) {
            primaryPanelTitle.textContent =
                actionType === "edit" ? "Update this request?" : "Delete this request?";
        }

        if (primaryNote) {
            primaryNote.textContent =
                actionType === "edit"
                    ? "If you update this request, the volunteer will be notified and your request will reopen so others can respond to the updated details."
                    : "If you delete this request, the volunteer will be notified that it is no longer needed, and the request will be removed.";
        }

        if (primaryConfirmBtn) {
            primaryConfirmBtn.textContent =
                actionType === "edit" ? "Continue to Edit" : "Confirm Delete";
        }

        if (primaryForm) {
            primaryForm.action = "";
        }
    }

    function showVerifyConfirm() {
        const item = modalState.item;
        if (!item) return;

        setPendingProcessingAction("verify");

        openPanel(primaryPanel, "primary", {
            clearContext: true
        });

        if (primaryTitle) {
            primaryTitle.textContent = item.title || "";
        }

        if (primaryItemId) {
            primaryItemId.value = item.itemId || "";
        }

        if (primaryReturnPageNumber) {
            primaryReturnPageNumber.value = getCurrentPageNumber();
        }

        if (primaryReturnQuery) {
            primaryReturnQuery.value = getCurrentReturnQuery();
        }

        if (primaryPanelTitle) {
            primaryPanelTitle.textContent = item.verifyPanelTitle || "Verify this item?";
        }

        if (primaryNote) {
            primaryNote.textContent = item.verifyNote || "Confirm that this item has been fulfilled.";
        }

        if (primaryConfirmBtn) {
            primaryConfirmBtn.textContent = "Verify Fulfillment";
        }

        if (primaryForm) {
            primaryForm.action = item.urls?.verify || "";
        }
    }

    function showVolunteerClaimedDeleteConfirm() {
        const item = modalState.item;
        if (!item) return;

        setPendingProcessingAction("delete");

        openPanel(primaryPanel, "primary", {
            clearContext: true
        });

        if (primaryTitle) {
            primaryTitle.textContent = item.title || "";
        }

        if (primaryItemId) {
            primaryItemId.value = item.itemId || "";
        }

        if (primaryReturnPageNumber) {
            primaryReturnPageNumber.value = getCurrentPageNumber();
        }

        if (primaryReturnQuery) {
            primaryReturnQuery.value = getCurrentReturnQuery();
        }

        if (primaryConfirmBtn) {
            if (item.actionMode === "volunteer_request_claimed") {
                primaryConfirmBtn.textContent = "Withdraw Claim";
            } else {
                primaryConfirmBtn.textContent = "Confirm Delete";
            }

            primaryConfirmBtn.classList.add("item-danger-btn");
        }

        if (item.actionMode === "volunteer_offer_claimed") {
            if (primaryPanelTitle) {
                primaryPanelTitle.textContent = "Delete this offer?";
            }

            if (primaryNote) {
                primaryNote.textContent =
                    "If you delete this offer, the unhoused user will be notified that it is no longer available.";
            }

            if (primaryForm) {
                primaryForm.action = item.urls?.delete || "";
            }

            return;
        }

        if (item.actionMode === "volunteer_request_claimed") {
            if (primaryPanelTitle) {
                primaryPanelTitle.textContent = "Remove yourself from this request?";
            }

            if (primaryNote) {
                primaryNote.textContent =
                    "If you remove yourself from this request, the unhoused user will be notified and the request will reopen so another volunteer can respond.";
            }

            if (primaryForm) {
                primaryForm.action = item.urls?.delete || "";
            }
        }
    }

    // Builds message context for owner vs claimer message flows.
    function buildMessagePanelContext(targetType) {
        const owner = getCurrentOwner();
        const claim = getCurrentClaim();

        if (targetType === "claimer") {
            return {
                targetType: "claimer",
                targetId: claim?.claimerId || "",
                targetName: claim?.claimedBy || ""
            };
        }

        return {
            targetType: "owner",
            targetId: owner?.id || "",
            targetName: owner?.name || ""
        };
    }

    // Shows the message panel for either the owner or the claimer.
    function showMessagePanelForTarget(targetType) {
        const item = modalState.item;
        if (!item) return;

        const panelName = targetType === "claimer"
            ? "message_claimer"
            : "message_owner";

        const currentPage = getCurrentPage();

        const fallbackReturnTo = targetType === "claimer"
            ? "my_offers"
            : (currentPage || "available_offers");

        const context = buildMessagePanelContext(targetType);

        setActivePanel(panelName);
        setPanelContext(context);
        hideAllPanels();
        showElement(messagePanel, "flex");
        resetMessagePanelState();

        const messageTarget = getCurrentMessageTarget();

        if (messageUserName) {
            messageUserName.textContent =
                messageTarget?.name || (targetType === "claimer" ? "Claimer" : "");
        }

        if (messageItemTitle) {
            messageItemTitle.textContent = item.title || "";
        }

        if (messageRecipientId) {
            messageRecipientId.value = messageTarget?.id || "";
        }

        if (messageReturnItemId) {
            messageReturnItemId.value = item.itemId || "";
        }

        if (messageReturnPage) {
            messageReturnPage.value = getCurrentPage();
        }

        if (messageReturnTo) {
            messageReturnTo.value = messageTarget?.returnTo || fallbackReturnTo;
        }

        if (messageReturnQuery) {
            messageReturnQuery.value = getCurrentReturnQuery();
        }

        if (messageReturnPageNumber) {
            messageReturnPageNumber.value = getCurrentPageNumber();
        }

        focusFieldLater(messageBody);
    }

    // Shortcut for opening the owner message panel.
    function showDefaultMessagePanel() {
        showMessagePanelForTarget("owner");
    }

    // Shortcut for opening the claimer message panel.
    function showClaimerMessagePanel() {
        showMessagePanelForTarget("claimer");
    }

    // Builds saved panel context for report workflows.
    function buildReportPanelContext(reportTarget) {
        return {
            targetType: reportTarget?.type || "",
            targetId: reportTarget?.itemId || "",
            targetName: reportTarget?.ownerName || ""
        };
    }

    // Fills report form fields and endpoints from the current report target.
    function applyReportPanelTarget(reportTarget) {
        if (!reportTarget) return;

        if (reportUserName) {
            reportUserName.textContent = reportTarget.ownerName || "";
        }

        if (reportUserId) {
            reportUserId.value = reportTarget.ownerId || "";
        }

        if (reportHeading) {
            reportHeading.textContent = reportTarget.heading || "Report Item";
        }

        if (reportForm) {
            reportForm.action = reportTarget.action || "";
        }

        if (reportReturnTo) {
            reportReturnTo.value = getCurrentPage() || "";
        }

        if (reportOfferId) {
            reportOfferId.value = "";
        }

        if (reportRequestId) {
            reportRequestId.value = "";
        }

        if (reportTarget.type === "request_report") {
            if (reportRequestId) {
                reportRequestId.value = reportTarget.itemId || "";
            }
        } else {
            if (reportOfferId) {
                reportOfferId.value = reportTarget.itemId || "";
            }
        }
    }

    // Shows the report panel for the active item.
    function showReportPanel() {
        const item = modalState.item;
        if (!item) return;

        const reportTarget = getCurrentReportTarget();

        setActivePanel("report");
        setPanelContext(buildReportPanelContext(reportTarget));
        hideAllPanels();
        showElement(reportPanel, "flex");
        resetReportPanelState();

        if (reportItemTitle) {
            reportItemTitle.textContent = item.title || "";
        }

        applyReportPanelTarget(reportTarget);
    }

    // Shows the edit panel and pre-fills it from the active item.
    function showEditPanel() {
        const item = modalState.item;
        if (!item) return;

        const isAdminAccount = isAdminAccountItem();

        openPanel(editPanel, "edit", {
            clearContext: true,
            resetPendingAction: true
        });

        if (editPanelTitle) {
            editPanelTitle.textContent = isAdminAccount
                ? `Edit Account: ${item.title || "Account"}`
                : `Edit ${item.title || "Item"}`;
        }

        if (isAdminAccount) {
            showElement(adminEditFields, "block");
            hideElement(standardEditFields);

            if (editTitle) editTitle.disabled = true;
            if (editCategory) editCategory.disabled = true;
            if (editCity) editCity.disabled = true;
            if (editLocation) editLocation.disabled = true;
            if (editDescription) editDescription.disabled = true;

            if (editDisplayUsername) editDisplayUsername.disabled = false;
            if (editFirstName) editFirstName.disabled = false;
            if (editLastName) editLastName.disabled = false;
            if (editEmail) editEmail.disabled = false;
            if (editPhone) editPhone.disabled = false;
            if (editAdminCity) editAdminCity.disabled = false;
            if (editState) editState.disabled = false;
            if (editRole) editRole.disabled = false;

            if (editDisplayUsername) editDisplayUsername.value = item.title || "";
            if (editFirstName) editFirstName.value = item.firstName || "";
            if (editLastName) editLastName.value = item.lastName || "";
            if (editEmail) editEmail.value = item.email || "";
            if (editPhone) editPhone.value = item.phone || "";
            if (editAdminCity) editAdminCity.value = item.city || "";
            if (editState) editState.value = item.state || "";
            if (editRole) editRole.value = (item.roleName || "").toLowerCase();
        } else {
            hideElement(adminEditFields);
            showElement(standardEditFields, "block");

            if (editDisplayUsername) editDisplayUsername.disabled = true;
            if (editFirstName) editFirstName.disabled = true;
            if (editLastName) editLastName.disabled = true;
            if (editEmail) editEmail.disabled = true;
            if (editPhone) editPhone.disabled = true;
            if (editAdminCity) editAdminCity.disabled = true;
            if (editState) editState.disabled = true;
            if (editRole) editRole.disabled = true;

            if (editTitle) editTitle.disabled = false;
            if (editCategory) editCategory.disabled = false;
            if (editCity) editCity.disabled = false;
            if (editLocation) editLocation.disabled = false;
            if (editDescription) editDescription.disabled = false;

            if (editTitle) {
                editTitle.value = item.title || "";

                editTitle.onkeydown = function (e) {
                    if (e.key === "Enter") {
                        e.preventDefault();
                    }
                };
            }
            if (editCategory) editCategory.value = item.categoryValue || "";
            if (editCity) editCity.value = item.city || "";
            if (editLocation) editLocation.value = item.location || "";
            if (editDescription) editDescription.value = item.description || "";
        }

        if (editReturnPageNumber) {
            editReturnPageNumber.value = getCurrentPageNumber();
        }

        if (editReturnQuery) {
            editReturnQuery.value = getCurrentReturnQuery();
        }

        if (editReturnItemId) {
            editReturnItemId.value = item.itemId || "";
        }

        const urls = getCurrentUrls();
        if (editForm) {
            editForm.action = urls.edit || "";
        }

        if (editTitle) {
            editTitle.dispatchEvent(new Event("input", { bubbles: true }));
            editTitle.dispatchEvent(new Event("blur", { bubbles: true }));
        }

        if (editCity) {
            editCity.dispatchEvent(new Event("input", { bubbles: true }));
            editCity.dispatchEvent(new Event("blur", { bubbles: true }));
        }
    }

    // Shows the delete confirm panel for the active item.
    function showDeletePanel() {
        const item = modalState.item;
        if (!item) return;

        const isAdminAccount = isAdminAccountItem();

        const deleteHeading = deletePanel.querySelector(".item-modal-title");
        if (deleteHeading) {
            deleteHeading.textContent = isAdminAccount
                ? "Delete This Account?"
                : "Delete This Offer?";
        }

        openPanel(deletePanel, "delete", {
            clearContext: true,
            resetPendingAction: true
        });

        if (deleteTitle) {
            deleteTitle.textContent = item.title || "";
        }

        const urls = getCurrentUrls();
        if (deleteForm) {
            deleteForm.action = urls.delete || "";
        }

        if (deleteReturnQuery) {
            deleteReturnQuery.value = getCurrentReturnQuery();
        }
    }

    // Hides a completed dashboard request locally after the user dismisses it.
    function hideCurrentDashboardRequest() {
        const item = modalState.item;
        if (!item || !item.itemId) return;

        const hiddenIds = getHiddenDashboardRequests();
        if (!hiddenIds.includes(item.itemId)) {
            hiddenIds.push(item.itemId);
            saveHiddenDashboardRequests(hiddenIds);
        }

        const card = findCardByItemId(item.itemId);

        if (card) {
            card.style.display = "none";
        }

        closeModal();
    }

    // Shows/hides footer action buttons based on normalized action flags.
    function configureActionButtons() {
        const item = modalState.item;
        const actions = getCurrentActions();

        hideElement(primaryBtn);
        hideElement(messageBtn);
        hideElement(reportBtn);
        hideElement(editBtn);
        hideElement(deleteBtn);
        hideElement(messageClaimerBtn);
        hideElement(verifyBtn);
        if (hideBtn) hideElement(hideBtn);

        if (!item) return;

        if (actions.showPrimary) {
            showElement(primaryBtn, "inline-flex");
        }

        if (actions.showMessageOwner) {
            showElement(messageBtn, "inline-flex");
        }

        if (actions.showReport) {
            showElement(reportBtn, "inline-flex");
        }

        if (actions.showEdit) {
            showElement(editBtn, "inline-flex");
        }

        if (actions.showDelete) {
            showElement(deleteBtn, "inline-flex");

            if (deleteBtn) {
                if (item.actionMode === "volunteer_request_claimed") {
                    deleteBtn.textContent = "Withdraw Claim";
                } else {
                    deleteBtn.textContent = "Delete";
                }
            }
        }

        if (actions.showMessageClaimer) {
            showElement(messageClaimerBtn, "inline-flex");
        }

        if (actions.showVerify) {
            showElement(verifyBtn, "inline-flex");
        }

        if (actions.showHide && hideBtn) {
            showElement(hideBtn, "inline-flex");
        }
    }

    // Main detail render step for the active modal item.
    // Populates title, owner, metadata, images, claim info, and action buttons.
    function populateModal() {
        const item = modalState.item;
        const owner = getCurrentOwner();
        const claim = getCurrentClaim();
        // const status = getCurrentStatus();

        if (!item) return;

        const isAdminAccount = isAdminAccountItem();

        setCurrentItem(item);
        resetImageState(item.images || []);
        setActivePanel("detail");

        if (modalTitle) modalTitle.textContent = item.title || "";

        if (modalOwnerPhoto) {
            if (owner?.photo) {
                modalOwnerPhoto.src = owner.photo;
                showElement(modalOwnerPhoto, "block");
                hideElement(modalOwnerInitials);
            } else {
                modalOwnerPhoto.removeAttribute("src");
                hideElement(modalOwnerPhoto);
                showElement(modalOwnerInitials, "inline-flex");

                if (modalOwnerInitials) {
                    modalOwnerInitials.textContent = owner?.initials || "";
                }
            }
        }

        if (modalOwnerName) modalOwnerName.textContent = owner?.name || "";

        if (modalOwnerTime) {
            modalOwnerTime.textContent = formatPostedDate(item.createdAt);
        }

        if (modalCategory) modalCategory.textContent = item.categoryLabel || "";
        if (modalCity) modalCity.textContent = item.city || "";
        if (modalLocation) modalLocation.textContent = item.location || "";

        if (modalStatus) {
            modalStatus.textContent = getCurrentStatus()?.displayText || "";
        }

        if (modalDescription) modalDescription.textContent = item.description || "";

        if (modalClaimedAtRow && modalClaimedAt) {
            if (claim?.claimedAt) {
                modalClaimedAt.textContent = formatPostedDate(claim.claimedAt);
                showElement(modalClaimedAtRow, "block");
            } else {
                modalClaimedAt.textContent = "";
                hideElement(modalClaimedAtRow);
            }
        }

        if (primaryBtn) {
            primaryBtn.textContent = getCurrentPrimaryLabel();
        }

        if (isAdminAccount) {
            hideElement(itemStandardUserBlock);
            hideElement(itemStandardMetaBlock);
            hideElement(itemStandardDescriptionBlock);
            showElement(itemAccountInfo, "block");
            hideElement(itemModalLeft);

            if (itemAccountUsername) itemAccountUsername.textContent = item.title || "Not provided";
            if (itemAccountFirstName) itemAccountFirstName.textContent = item.firstName || "Not provided";
            if (itemAccountLastName) itemAccountLastName.textContent = item.lastName || "Not provided";
            if (itemAccountEmail) itemAccountEmail.textContent = item.email || "Not provided";
            if (itemAccountPhone) itemAccountPhone.textContent = item.phone || "Not provided";
            if (itemAccountCity) itemAccountCity.textContent = item.city || "Not provided";
            if (itemAccountState) itemAccountState.textContent = item.state || "Not provided";
            if (itemAccountRole) itemAccountRole.textContent = item.roleName || "None";
            if (itemAccountJoined) itemAccountJoined.textContent = formatPostedDate(item.createdAt);

            hideElement(modalEmailRow);
            hideElement(modalPhoneRow);
            hideElement(modalRoleRow);
        } else {
            showElement(itemStandardUserBlock, "flex");
            showElement(itemStandardMetaBlock, "block");
            showElement(itemStandardDescriptionBlock, "block");
            hideElement(itemAccountInfo);
            showElement(itemModalLeft, "grid");

            hideElement(modalEmailRow);
            hideElement(modalPhoneRow);
            hideElement(modalRoleRow);
        }

        updateImageView();
        configureActionButtons();
        showDetailPanel();
    }

    // ============================================================
    // CARD DATA NORMALIZATION
    // Converts raw card data-* attributes into one consistent modal item.
    // This is the bridge between HTML card markup and modal state.
    //
    // Edit here if you add:
    // - new card data fields
    // - new action modes
    // - new button visibility rules
    // - new item metadata shown in the modal
    // ============================================================

    // Build one normalized item object from the clicked card.
    function buildCardData(card) {
        const parsedImages = parseImages(card.dataset.images);

        const rawStatusLabel = card.dataset.status || "";
        const claimedBy = card.dataset.claimedBy || "";
        const normalizedStatusCode = rawStatusLabel.trim().toLowerCase();

        const status = {
            code: normalizedStatusCode,
            label: rawStatusLabel,
            actorName: claimedBy,
            displayText: rawStatusLabel
        };

        if (claimedBy) {
            status.displayText = `${rawStatusLabel} by ${claimedBy}`;
        }

        const actionMode = card.dataset.actionMode || "";
        const isAdminAccount = actionMode === "admin_account";
        const hasClaimer = !!(card.dataset.claimerId || "");

        const actions = {
            showPrimary: false,
            showMessageOwner: false,
            showReport: false,
            showEdit: false,
            showDelete: false,
            showMessageClaimer: false,
            showVerify: false,
            showHide: false,
            requiresProcessingConfirm: false
        };

        if (isAdminAccount) {
            actions.showEdit = true;
            actions.showDelete = card.dataset.canDelete === "true";
        } else if (actionMode === "mine") {
            actions.showDelete = true;

            if (hasClaimer) {
                actions.showMessageClaimer = true;
            } else {
                actions.showEdit = true;
            }
        } else if (actionMode === "request_open") {
            actions.showEdit = true;
            actions.showDelete = true;
        } else if (actionMode === "request_processing") {
            actions.showEdit = true;
            actions.showMessageClaimer = hasClaimer;
            actions.showVerify = true;
            actions.showDelete = true;
            actions.requiresProcessingConfirm = true;
        } else if (actionMode === "volunteer_request_claimed") {
            actions.showMessageOwner = true;
            actions.showDelete = true;
        } else if (actionMode === "volunteer_request_completed") {
            actions.showMessageOwner = true;
            actions.showHide = true;
        } else if (actionMode === "volunteer_offer_claimed") {
            actions.showMessageClaimer = hasClaimer;
            actions.showVerify = true;
            actions.showDelete = true;
        } else if (actionMode === "request_completed") {
            actions.showMessageClaimer = hasClaimer;
            actions.showHide = true;
        } else {
            actions.showPrimary = true;
            actions.showMessageOwner = true;
            actions.showReport = true;
        }

        const owner = {
            id: card.dataset.ownerId || "",
            reportId: card.dataset.ownerReportId || "",
            name: card.dataset.ownerName || "",
            initials: card.dataset.ownerInitials || "",
            photo: card.dataset.ownerPhoto || ""
        };

        const claim = {
            claimerId: card.dataset.claimerId || "",
            claimedBy: claimedBy,
            claimedAt: card.dataset.claimedAt || ""
        };

        const urls = {
            primary: card.dataset.primaryUrl || "",
            edit: card.dataset.editUrl || "",
            delete: card.dataset.deleteUrl || "",
            verify: ""
        };

        let verifyPanelTitle = "";
        let verifyNote = "";

        if (actionMode === "volunteer_offer_claimed") {
            urls.verify = `/offers/${card.dataset.itemId}/verify/`;
            verifyPanelTitle = "Verify this offer?";
            verifyNote = "Confirm that this offer has been fulfilled.";
        } else if (actionMode === "volunteer_request_claimed" || actionMode === "request_processing") {
            urls.verify = `/requests/${card.dataset.itemId}/verify/`;
            verifyPanelTitle = "Verify this request?";
            verifyNote = "Confirm that this request has been fulfilled.";
        }

        return {
            itemId: card.dataset.itemId || "",
            currentUserId: card.dataset.currentUserId || "",
            title: card.dataset.title || "",
            categoryLabel: card.dataset.category || "",
            categoryValue: card.dataset.categoryValue || "",
            city: card.dataset.city || "",
            status: status,
            description: card.dataset.description || "",
            location: card.dataset.location || "",
            createdAt: card.dataset.created || "",
            email: card.dataset.email || "",
            phone: card.dataset.phone || "",
            roleName: card.dataset.roleName || "",
            firstName: card.dataset.firstName || "",
            lastName: card.dataset.lastName || "",
            state: card.dataset.state || "",

            owner: owner,
            claim: claim,
            urls: urls,
            actions: actions,

            images: isAdminAccount
                ? []
                : (parsedImages.length
                    ? parsedImages
                    : [getDefaultCategoryImage(card.dataset.categoryValue, card.dataset.category)]),

            actionMode: actionMode,
            primaryLabel: card.dataset.primaryLabel || "",
            messageLabel: card.dataset.messageLabel || "",
            reportLabel: card.dataset.reportLabel || "",
            primaryPanelTitle: card.dataset.primaryPanelTitle || "",
            primaryConfirmLabel: card.dataset.primaryConfirmLabel || "",
            primaryNote: card.dataset.primaryNote || "",
            verifyPanelTitle: verifyPanelTitle,
            verifyNote: verifyNote,
        };
    }

    // ============================================================
    // MODAL LIFECYCLE
    // Open, close, and initialize the reusable modal.
    // ============================================================

    // Opens the modal from a clicked card by normalizing its data into state.
    function openModal(card) {
        const item = buildCardData(card);

        setCurrentItem(item);
        resetImageState(item.images || []);
        setPendingProcessingAction(null);
        setActivePanel("detail");

        populateModal();
        modal.classList.add("open");
        document.body.style.overflow = "hidden";
    }

    // Closes the modal and resets it back to its default state.
    function closeModal() {
        modal.classList.remove("open");
        document.body.style.overflow = "";

        resetModalState();

        clearThumbs();
        clearPanelErrors();
        showDetailPanel();
    }

    // ============================================================
    // FORM SUBMIT / VALIDATION HANDLERS
    // Client-side validation before modal forms are submitted.
    // ============================================================

    // Validates message submit state before allowing the form to post.
    function handleMessageSubmit(e) {
        const bodyValue = messageBody ? messageBody.value.trim() : "";

        if (!bodyValue) {
            e.preventDefault();
            showElement(messageError, "block");

            if (messageBody) {
                messageBody.focus();
            }
            return;
        }

        const item = getCurrentItem();
        sessionStorage.setItem("itemModalScrollY", String(window.scrollY));
        sessionStorage.setItem("itemModalReturnItemId", item?.itemId || "");
    }

    function handleReportSubmit(e) {
        const item = getCurrentItem();
        const reportTarget = getCurrentReportTarget();

        if (!reportReason || !reportReason.value) {
            e.preventDefault();
            if (reportError) {
                reportError.textContent = "Please choose a reason.";
                showElement(reportError, "block");
            }
            return;
        }

        const targetId = isCurrentItemRequest()
            ? (reportRequestId ? reportRequestId.value.trim() : "")
            : (reportOfferId ? reportOfferId.value.trim() : "");

        const reportedUserId = reportUserId ? reportUserId.value.trim() : "";

        if (!reportTarget || !reportTarget.itemId || !reportTarget.ownerId) {
            e.preventDefault();
            if (reportError) {
                reportError.textContent = "Could not submit this report. Please close the modal and try again.";
                showElement(reportError, "block");
            }
            return;
        }

        if (
            String(targetId) !== String(reportTarget.itemId) ||
            String(reportedUserId) !== String(reportTarget.ownerId)
        ) {
            e.preventDefault();
            if (reportError) {
                reportError.textContent = "Could not submit this report. Please close the modal and try again.";
                showElement(reportError, "block");
            }
            return;
        }

        if (item?.itemId) {
            saveReturnItemState(item.itemId);
        }

    }

    function handleEditSubmit(e) {
        if (isAdminAccountItem()) {
            sessionStorage.setItem("itemModalScrollY", String(window.scrollY));
            sessionStorage.setItem("itemModalReturnItemId", modalState.item?.itemId || "");
            return;
        }

        const titleValue = editTitle ? editTitle.value.trim() : "";
        const cityValue = editCity ? editCity.value.trim() : "";

        let hasError = false;

        editTitle?.dispatchEvent(new Event("input", { bubbles: true }));
        editTitle?.dispatchEvent(new Event("blur", { bubbles: true }));

        editCity?.dispatchEvent(new Event("input", { bubbles: true }));
        editCity?.dispatchEvent(new Event("blur", { bubbles: true }));

        if (typeof isValidItemTitle === "function" && !isValidItemTitle(titleValue, 60)) {
            hasError = true;
        }

        if (typeof isValidItemCity === "function" && !isValidItemCity(cityValue, 25)) {
            hasError = true;
        }

        if (hasError) {
            e.preventDefault();

            if (typeof isValidItemTitle === "function" && !isValidItemTitle(titleValue, 60)) {
                editTitle?.focus();
            } else if (typeof isValidItemCity === "function" && !isValidItemCity(cityValue, 25)) {
                editCity?.focus();
            }

            return;
        }

        sessionStorage.setItem("itemModalScrollY", String(window.scrollY));
        sessionStorage.setItem("itemModalReturnItemId", modalState.item?.itemId || "");
    }

    function isAdminAccountItem() {
        return (modalState.item?.actionMode || "") === "admin_account";
    }

    const hiddenIds = getHiddenDashboardRequests();
    cards.forEach(card => {
        if (hiddenIds.includes(card.dataset.itemId) && card.dataset.actionMode === "request_completed") {
            card.style.display = "none";
        }

        card.addEventListener("click", function () {
            openModal(card);
        });
    });

    if (primaryBtn) {
        primaryBtn.addEventListener("click", function (e) {
            e.stopPropagation();
            showPrimaryPanel();
        });
    }

    if (messageBtn) {
        messageBtn.addEventListener("click", function (e) {
            e.stopPropagation();
            showDefaultMessagePanel();
        });
    }

    if (messageClaimerBtn) {
        messageClaimerBtn.addEventListener("click", function (e) {
            e.stopPropagation();
            showClaimerMessagePanel();
        });
    }

    if (verifyBtn) {
        verifyBtn.onclick = function (e) {
            e.stopPropagation();
            showVerifyConfirm();
        };
    }

    if (reportBtn) {
        reportBtn.addEventListener("click", function (e) {
            e.stopPropagation();
            showReportPanel();
        });
    }

    if (editBtn) {
        editBtn.addEventListener("click", function (e) {
            e.stopPropagation();

            const item = getCurrentItem();
            if (!item) return;

            if (item.actions?.requiresProcessingConfirm) {
                showProcessingRequestConfirm("edit");
                return;
            }

            showEditPanel();
        });
    }

    if (deleteBtn) {
        deleteBtn.addEventListener("click", function (e) {
            e.stopPropagation();

            const item = getCurrentItem();
            if (!item) return;

            if (
                item.actionMode === "volunteer_request_claimed" ||
                item.actionMode === "volunteer_offer_claimed"
            ) {
                showVolunteerClaimedDeleteConfirm();
                return;
            }

            if (item.actions?.requiresProcessingConfirm) {
                showProcessingRequestConfirm("delete");
                return;
            }

            showDeletePanel();
        });
    }

    if (hideBtn) {
        hideBtn.addEventListener("click", function (e) {
            e.stopPropagation();
            hideCurrentDashboardRequest();
        });
    }

    if (primaryForm) {
        primaryForm.addEventListener("submit", function (e) {

            const item = getCurrentItem();
            const pendingAction = getPendingProcessingAction();

            if (!item || !item.actions?.requiresProcessingConfirm) {
                return;
            }

            if (pendingAction === "verify") {
                return;
            }

            e.preventDefault();

            if (pendingAction === "edit") {
                showEditPanel();
                return;
            }

            if (pendingAction === "delete") {
                if (deleteForm) {
                    const urls = getCurrentUrls();
                    deleteForm.action = urls.delete || "";

                    if (deleteReturnQuery) {
                        deleteReturnQuery.value = getCurrentReturnQuery();
                    }

                    deleteForm.submit();
                }
            }
        });
    }

    if (primaryBackBtn) primaryBackBtn.addEventListener("click", showDetailPanel);
    if (messageBackBtn) messageBackBtn.addEventListener("click", showDetailPanel);
    if (reportBackBtn) reportBackBtn.addEventListener("click", showDetailPanel);
    if (editBackBtn) editBackBtn.addEventListener("click", showDetailPanel);
    if (deleteBackBtn) deleteBackBtn.addEventListener("click", showDetailPanel);

    if (messageForm) messageForm.addEventListener("submit", handleMessageSubmit);
    if (reportForm) reportForm.addEventListener("submit", handleReportSubmit);
    if (editForm) editForm.addEventListener("submit", handleEditSubmit);

    if (prevBtn) {
        prevBtn.addEventListener("click", function (e) {
            e.stopPropagation();
            showPreviousImage();
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener("click", function (e) {
            e.stopPropagation();
            showNextImage();
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener("click", closeModal);
    }

    modal.addEventListener("click", function (e) {
        if (e.target === modal) {
            closeModal();
        }
    });

    document.addEventListener("keydown", function (e) {
        //const images = getCurrentImages();

        if (!modal.classList.contains("open")) return;

        if (e.key === "Escape") {
            closeModal();
        } else if (e.key === "ArrowLeft" && hasMultipleImages()) {
            showPreviousImage();
        } else if (e.key === "ArrowRight" && hasMultipleImages()) {
            showNextImage();
        }
    });
});