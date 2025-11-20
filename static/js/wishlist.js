// ====================================================
// 0) THEME-BASED EMOJI CONTROLLER
// ====================================================
function getEmptyHeartEmoji() {
    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    return isDark ? "🤍" : "🤍";
}

function applyHeartEmoji(btn) {
    if (btn.classList.contains("added")) {
        btn.innerHTML = "❤️";
    } else {
        btn.innerHTML = getEmptyHeartEmoji();
    }
}

// ====================================================
// 1) Pre-fill hearts + Load wishlist count
// ====================================================
document.addEventListener("DOMContentLoaded", () => {
    // Auto-fill hearts
    fetch("/wishlist/ids")
        .then(res => res.json())
        .then(data => {
            const ids = data.ids || [];
            document.querySelectorAll(".wishlist-heart").forEach(btn => {
                if (ids.includes(parseInt(btn.dataset.productId))) {
                    btn.classList.add("added");
                }
                applyHeartEmoji(btn);
            });
        })
        .catch(err => console.error("Wishlist preload error:", err));

    // Load count
    fetch("/wishlist/count")
        .then(res => res.json())
        .then(data => updateWishlistBadge(data.count || 0))
        .catch(err => console.error("Wishlist count error:", err));
});

// ====================================================
// GLOBAL: Wishlist Badge Update
// ====================================================
function updateWishlistBadge(count) {
    const badge = document.getElementById("wishlist-count-badge");
    if (!badge) return;
    badge.textContent = count;
    badge.style.display = count > 0 ? "inline-block" : "none";
}

// ====================================================
// 2) CLICK HANDLER FOR HEARTS + REMOVE BUTTONS
// ====================================================
document.addEventListener("click", async (e) => {
    const heartBtn = e.target.closest(".wishlist-heart");
    const removeBtn = e.target.closest(".remove-wishlist-item");

    if (heartBtn) {
        await toggleWishlistHeart(heartBtn);
        return;
    }

    if (removeBtn) {
        await removeFromWishlistPage(removeBtn);
        return;
    }
});

// ====================================================
// 3) ADD / REMOVE HEART TOGGLE (PRODUCT PAGE)
// ====================================================
async function toggleWishlistHeart(btn) {
    const productId = btn.dataset.productId;
    if (!productId) return;

    if (btn.dataset.busy === "1") return;
    btn.dataset.busy = "1";

    const isAdded = btn.classList.contains("added");
    const url = isAdded ? "/wishlist/remove" : "/wishlist/add";

    const original = btn.innerHTML;
    btn.style.transform = "scale(0.92)";

    try {
        const res = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ product_id: productId }),
        });

        const data = await res.json().catch(() => null);

        if (res.ok && data?.count !== undefined) {

            // REMOVE
            if (isAdded) {
                btn.classList.remove("added");
                showNotification("Removed from wishlist", "info");
            }

            // ADD
            else {
                btn.classList.add("added");
                showNotification("Added to wishlist ✓", "success");
            }

            // Update count badge
            updateWishlistBadge(data.count);

            // New emoji system
            applyHeartEmoji(btn);

            // Animation
            btn.classList.add("pop");
            if (btn.classList.contains("added")) {
                btn.classList.add("pulse");
            }

            setTimeout(() => btn.classList.remove("pop", "pulse"), 350);

        } else {
            btn.innerHTML = original;
            showNotification("Action failed", "error");
        }

    } catch (err) {
        console.error(err);
        btn.innerHTML = original;
        showNotification("Network error", "error");
    }

    btn.dataset.busy = "0";
    btn.style.transform = "";
}

// ====================================================
// 4) REMOVE FROM WISHLIST PAGE
// ====================================================
async function removeFromWishlistPage(btn) {
    const productId = btn.dataset.productId;
    if (!productId) return;

    btn.disabled = true;
    btn.textContent = "Removing...";

    try {
        const res = await fetch("/wishlist/remove", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ product_id: productId }),
        });

        const data = await res.json().catch(() => null);

        if (res.ok && data?.count !== undefined) {
            updateWishlistBadge(data.count);
            showNotification("Removed from wishlist", "info");

            const card = btn.closest(".wishlist-card");
            if (card) card.remove();
        } else {
            btn.disabled = false;
            btn.textContent = "Remove";
            showNotification("Failed to remove", "error");
        }

    } catch {
        btn.disabled = false;
        btn.textContent = "Remove";
        showNotification("Network error", "error");
    }
}

// ====================================================
// 5) Toast Notification
// ====================================================
function showNotification(message, type = "success") {
    const box = document.createElement("div");
    box.className = `alert alert--${type}`;
    box.textContent = message;
    box.style.cssText =
        "position:fixed; top:88px; right:16px; z-index:1100; min-width:160px;";
    document.body.appendChild(box);

    setTimeout(() => {
        box.style.opacity = "0";
        box.style.transition = "opacity 250ms";
        setTimeout(() => box.remove(), 300);
    }, 2000);
}

// ====================================================
// 6) APPLY HEART EMOJI ON THEME TOGGLE
// ====================================================
const themeToggle = document.getElementById("theme-toggle");
if (themeToggle) {
    themeToggle.addEventListener("change", () => {
        document.querySelectorAll(".wishlist-heart").forEach(btn => {
            applyHeartEmoji(btn);
        });
    });
}
