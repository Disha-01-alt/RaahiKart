// --- Global Configuration ---
const API_BASE_URL = 'http://127.0.0.1:5000/api';

// ######################################################################
// ### IMPORTANT: FILL IN YOUR KEYS IN THE PLACEHOLDERS BELOW ###
// ######################################################################

// IMPORTANT: Replace with your actual Firebase and Google Maps configuration
 const firebaseConfig = {
  apiKey: "AIzaSyCY7y_Yumz4C11ncLyhg3HeoigmEWO6dA8",
  authDomain: "raahikart-f0282.firebaseapp.com",
  databaseURL: "https://raahikart-f0282-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "raahikart-f0282",
  storageBucket: "raahikart-f0282.firebasestorage.app",
  messagingSenderId: "588579447817",
  appId: "1:588579447817:web:1b045eed89000038bd84d8",
  measurementId: "G-R3ZGVZJ7Y3"
};

const GOOGLE_MAPS_API_KEY = 'AIzaSyD5aOtlSIu0sCfxeielmAW-V2BIUSCNFBg'; // From Google Cloud Console
const RECAPTCHA_V3_SITE_KEY = '6LetwZsrAAAAAP7Q4hqbYxok7UOb_alEWJA5txwd'; // From reCAPTCHA Admin Console

// ######################################################################

// --- Firebase Initialization ---
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const db = firebase.firestore();

// --- Helper Functions ---

/**
 * Shows a simple notification.
 */
function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] - ${message}`);
    alert(`[${type.toUpperCase()}] - ${message}`);
}

/**
 * Handles user logout.
 */
function logout() {
    auth.signOut().then(() => {
        localStorage.removeItem('raahikartIdToken');
        showNotification('Logged out successfully', 'success');
        window.location.href = 'index.html';
    }).catch((error) => {
        showNotification('Error logging out: ' + error.message, 'error');
    });
}

/**
 * Dynamically loads the Google Maps script and sets the callback.
 */
 // Add this Haversine distance function to your scripts.js file
function getDistanceFromLatLonInKm(lat1, lon1, lat2, lon2) {
    const R = 6371; // Radius of the earth in km
    const dLat = (lat2 - lat1) * (Math.PI / 180);
    const dLon = (lon2 - lon1) * (Math.PI / 180);
    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const d = R * c; // Distance in km
    return d;
}
function loadGoogleMapsScript() {
    if (document.getElementById('google-maps-script')) {
        return; // Script already loaded
    }
    const script = document.createElement('script');
    script.id = 'google-maps-script';
    // This URL includes the "callback=initMap" parameter, which is crucial.
    script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&libraries=places&callback=initMap`;
    script.async = true;
    script.defer = true;
    script.onerror = function() {
        showNotification("Failed to load Google Maps script. Please check your API key, billing status, and enabled APIs in the Google Cloud Console.", "error");
    };
    document.head.appendChild(script);
}
