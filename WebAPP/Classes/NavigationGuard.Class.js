import { Message } from "./Message.Class.js";

let activeGuard = null;
let leaveRequestPending = false;

// Warn before reloading or closing a page with unsaved changes
function handleBeforeUnload(event) {
    if (!activeGuard || !activeGuard.hasChanges()) {
        return;
    }

    event.preventDefault();
    event.returnValue = "";
}

// Controls whether the user can leave a page with unsaved changes
export class NavigationGuard {
    // Starts checking the current page for unsaved changes
    static activate(handlers) {
        activeGuard = handlers;
        leaveRequestPending = false;
        window.addEventListener("beforeunload", handleBeforeUnload);
    }

    // Stops checking after the user leaves the page
    static deactivate() {
        activeGuard = null;
        leaveRequestPending = false;
        window.removeEventListener("beforeunload", handleBeforeUnload);
    }

    // Checks whether the user can leave, then continues when allowed
    static async requestLeave(onAllowed, onBlocked = () => {}) {
        if (!activeGuard) {
            onAllowed();
            return;
        }

        if (leaveRequestPending) {
            return;
        }

        if (!activeGuard.hasChanges()) {
            NavigationGuard.deactivate();
            onAllowed();
            return;
        }

        leaveRequestPending = true;

        // Wait for the user to choose whether to save or leave
        try {
            const choice = await Message.confirmUnsavedModelChanges();

            if (choice === "Don't save") {
                NavigationGuard.deactivate();
                onAllowed();
                return;
            }

            if (choice === "Save") {
                activeGuard.update();
                onBlocked();
            }
        } finally {
            leaveRequestPending = false;
        }
    }
}
