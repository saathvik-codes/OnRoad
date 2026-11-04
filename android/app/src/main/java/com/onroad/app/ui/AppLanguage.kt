package com.onroad.app.ui

import android.content.Context
import android.content.SharedPreferences
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Check
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material3.BasicAlertDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.flow.MutableStateFlow

data class SupportedLanguage(
    val code: String,
    val name: String,
    val nativeName: String,
    val flag: String
)

object AppLanguage {
    private var prefs: SharedPreferences? = null
    val currentLanguage = MutableStateFlow("en")

    val languages = listOf(
        SupportedLanguage("en", "English", "English", "🌐"),
        SupportedLanguage("hi", "Hindi", "हिन्दी", "🇮🇳"),
        SupportedLanguage("te", "Telugu", "తెలుగు", "🇮🇳"),
        SupportedLanguage("ta", "Tamil", "தமிழ்", "🇮🇳"),
        SupportedLanguage("kn", "Kannada", "ಕನ್ನಡ", "🇮🇳"),
        SupportedLanguage("ml", "Malayalam", "മലയാളം", "🇮🇳"),
        SupportedLanguage("mr", "Marathi", "मराठी", "🇮🇳"),
        SupportedLanguage("bn", "Bengali", "বাংলা", "🇮🇳"),
        SupportedLanguage("gu", "Gujarati", "ગુજરાતી", "🇮🇳"),
        SupportedLanguage("pa", "Punjabi", "ਪੰਜਾਬੀ", "🇮🇳"),
        SupportedLanguage("es", "Spanish", "Español", "🇪🇸"),
        SupportedLanguage("fr", "French", "Français", "🇫🇷"),
        SupportedLanguage("de", "German", "Deutsch", "🇩🇪"),
        SupportedLanguage("ar", "Arabic", "العربية", "🇸🇦")
    )

    fun init(ctx: Context) {
        prefs = ctx.getSharedPreferences("onroad_lang", Context.MODE_PRIVATE)
        val saved = prefs?.getString("lang", null)
        if (saved != null) {
            currentLanguage.value = saved
        } else {
            val sysLang = java.util.Locale.getDefault().language
            if (languages.any { it.code == sysLang }) {
                currentLanguage.value = sysLang
            } else {
                currentLanguage.value = "en"
            }
        }
    }

    fun set(code: String) {
        currentLanguage.value = code
        prefs?.edit()?.putString("lang", code)?.apply()
    }

    fun name(code: String): String {
        return languages.firstOrNull { it.code == code }?.let { "${it.nativeName} (${it.name})" } ?: code
    }

    fun shortName(code: String): String {
        return languages.firstOrNull { it.code == code }?.nativeName ?: code
    }

    fun translate(key: String, lang: String = currentLanguage.value): String {
        if (lang == "en") return key
        return DICTIONARY[lang]?.get(key) ?: key
    }

    private val DICTIONARY: Map<String, Map<String, String>> = mapOf(
        "hi" to mapOf(
            "Home" to "होम",
            "Explore" to "एक्सप्लोर करें",
            "Offers" to "ऑफ़र्स",
            "Calculator" to "कैलकुलेटर",
            "Profile" to "प्रोफ़ाइल",
            "Preferences" to "प्राथमिकताएं",
            "Language" to "भाषा",
            "Appearance" to "दिखावट",
            "City for prices" to "कीमतों के लिए शहर",
            "Offers & launch alerts" to "ऑफ़र और लॉन्च अलर्ट",
            "Buying guide" to "खरीद गाइड",
            "Where prices come from" to "कीमतें कहाँ से आती हैं",
            "App version" to "ऐप संस्करण",
            "Saved cars" to "सहेजी गई कारें",
            "My dealer quotes" to "मेरे डीलर कोट्स",
            "Sign in or create account" to "साइन इन करें या खाता बनाएं",
            "Sign out" to "साइन आउट करें",
            "Find my car" to "मेरी कार ढूंढें",
            "Find my bike" to "मेरी बाइक ढूंढें",
            "Showrooms near me" to "पास के शोरूम",
            "Compare" to "तुलना करें",
            "Cars" to "कारें",
            "Bikes" to "बाइक",
            "Shop by budget" to "बजट के अनुसार खरीदें",
            "Top buys in India" to "भारत में सबसे ज्यादा बिकने वाली",
            "Top picks to compare" to "तुलना के लिए शीर्ष विकल्प",
            "See all" to "सभी देखें",
            "Saved" to "सहेजे गए",
            "Requests" to "अनुरोध",
            "Replies" to "उत्तर",
            "Auto" to "ऑटो",
            "Light" to "लाइट",
            "Dark" to "डार्क",
            "Same as phone" to "फ़ोन के समान",
            "Your garage is empty" to "आपका गैरेज खाली है",
            "Manufacturer offers and newly listed models" to "निर्माता ऑफ़र और नए सूचीबद्ध मॉडल",
            "From quote to number plate, step by step" to "कोट से नंबर प्लेट तक, कदम दर कदम",
            "Price on request" to "अनुरोध पर कीमत",
            "On-road price" to "ऑन-रोड कीमत",
            "Ex-showroom" to "एक्स-शोरूम"
        ),
        "te" to mapOf(
            "Home" to "హోమ్",
            "Explore" to "ఎక్స్‌ప్లోర్",
            "Offers" to "ఆఫర్లు",
            "Calculator" to "క్యాలిక్యులేటర్",
            "Profile" to "ప్రొఫైల్",
            "Preferences" to "ప్రాధాన్యతలు",
            "Language" to "భాష",
            "Appearance" to "రూపం",
            "City for prices" to "ధరల కోసం నగరం",
            "Offers & launch alerts" to "ఆఫర్లు & లాంచ్ హెచ్చరికలు",
            "Buying guide" to "కొనుగోలు గైడ్",
            "Where prices come from" to "ధరల మూలం",
            "App version" to "యాప్ వెర్షన్",
            "Saved cars" to "సేవ్ చేసిన కార్లు",
            "My dealer quotes" to "డీలర్ కొటేషన్లు",
            "Sign in or create account" to "సైన్ ఇన్ లేదా ఖాతా తెరవండి",
            "Sign out" to "సైన్ అవుట్",
            "Find my car" to "నా కారును కనుగొనండి",
            "Find my bike" to "నా బైక్‌ను కనుగొనండి",
            "Showrooms near me" to "సమీప షోరూమ్‌లు",
            "Compare" to "పోల్చండి",
            "Cars" to "కార్లు",
            "Bikes" to "బైకులు",
            "Shop by budget" to "బడ్జెట్ ప్రకారం కొనండి",
            "Top buys in India" to "భారతదేశంలో టాప్ అమ్మకాలు",
            "Top picks to compare" to "పోల్చడానికి టాప్ ఎంపికలు",
            "See all" to "అన్నీ చూడండి",
            "Saved" to "సేవ్ చేసినవి",
            "Requests" to "అభ్యర్థనలు",
            "Replies" to "సమాధానాలు",
            "Auto" to "ఆటో",
            "Light" to "లైట్",
            "Dark" to "డార్క్",
            "Same as phone" to "ఫోన్ లాగా",
            "Your garage is empty" to "మీ గ్యారేజ్ ఖాళీగా ఉంది"
        ),
        "ta" to mapOf(
            "Home" to "முகப்பு",
            "Explore" to "ஆராயுங்கள்",
            "Offers" to "சலுகைகள்",
            "Calculator" to "கால்குலேட்டர்",
            "Profile" to "சுயவிவரம்",
            "Preferences" to "விருப்பத்தேர்வுகள்",
            "Language" to "மொழி",
            "Appearance" to "தோற்றம்",
            "City for prices" to "விலைகளுக்கான நகரம்",
            "Offers & launch alerts" to "சலுகைகள் & அறிவிப்புகள்",
            "Buying guide" to "வாங்கும் வழிகாட்டி",
            "Where prices come from" to "விலை விவரங்கள்",
            "App version" to "செயலி பதிப்பு",
            "Saved cars" to "சேமிக்கப்பட்ட கார்கள்",
            "My dealer quotes" to "டீலர் விலைக் குறிப்புகள்",
            "Sign in or create account" to "உள்நுழையவும் அல்லது கணக்கு தொடங்கவும்",
            "Sign out" to "வெளியேறு",
            "Find my car" to "என் காரைக் கண்டுபிடி",
            "Find my bike" to "என் பைக்கைக் கண்டுபிடி",
            "Showrooms near me" to "அருகிலுள்ள ஷோரூம்கள்",
            "Compare" to "ஒப்பிடு",
            "Cars" to "கார்கள்",
            "Bikes" to "பைக்குகள்",
            "Shop by budget" to "பட்ஜெட் மூலம் தேர்வு",
            "Top buys in India" to "இந்தியாவில் அதிகம் விற்பனையாகும்",
            "Top picks to compare" to "ஒப்பிட சிறந்த தேர்வுகள்",
            "See all" to "அனைத்தையும் பார்",
            "Saved" to "சேமிக்கப்பட்டது",
            "Requests" to "கோரிக்கைகள்",
            "Replies" to "பதில்கள்",
            "Auto" to "தானியங்கி",
            "Light" to "வெளிச்சம்",
            "Dark" to "இருள்",
            "Same as phone" to "போனைப் போலவே"
        ),
        "kn" to mapOf(
            "Home" to "ಮುಖಪುಟ",
            "Explore" to "ಅನ್ವೇಷಿಸಿ",
            "Offers" to "ಆಫರ್‌ಗಳು",
            "Calculator" to "ಕ್ಯಾಲ್ಕುಲೇಟರ್",
            "Profile" to "ಪ್ರೊಫೈಲ್",
            "Preferences" to "ಆದ್ಯತೆಗಳು",
            "Language" to "ಭಾಷೆ",
            "Appearance" to "ಗೋಚರತೆ",
            "City for prices" to "ಬೆಲೆಗಳಿಗಾಗಿ ನಗರ",
            "Offers & launch alerts" to "ಆಫರ್ & ಬಿಡುಗಡೆ ಎಚ್ಚರಿಕೆಗಳು",
            "Buying guide" to "ಖರೀದಿ ಮಾರ್ಗದರ್ಶಿ",
            "Saved cars" to "ಉಳಿಸಿದ ಕಾರುಗಳು",
            "Sign in or create account" to "ಸೈನ್ ಇನ್ ಮಾಡಿ ಅಥವಾ ಖಾತೆ ರಚಿಸಿ",
            "Sign out" to "ಸೈನ್ ಔಟ್",
            "Find my car" to "ನನ್ನ ಕಾರನ್ನು ಹುಡುಕಿ",
            "Showrooms near me" to "ಹತ್ತಿರದ ಶೋರೂಮ್‌ಗಳು",
            "Compare" to "ಹೋಲಿಕೆ ಮಾಡಿ",
            "Cars" to "ಕಾರುಗಳು",
            "Bikes" to "ಬೈಕ್‌ಗಳು"
        ),
        "ml" to mapOf(
            "Home" to "ഹോം",
            "Explore" to "എക്സ്പ്ലോർ",
            "Offers" to "ഓഫറുകൾ",
            "Calculator" to "കാൽക്കുലേറ്റർ",
            "Profile" to "പ്രൊഫൈൽ",
            "Preferences" to "മുൻഗണനകൾ",
            "Language" to "ഭാഷ",
            "Appearance" to "രൂപഭാവം",
            "City for prices" to "വിലകൾക്കുള്ള നഗരം",
            "Buying guide" to "വാങ്ങൽ ഗൈഡ്",
            "Saved cars" to "സൂക്ഷിച്ച കാറുകൾ",
            "Sign in or create account" to "സൈൻ ഇൻ ചെയ്യുക",
            "Sign out" to "സൈൻ ഔട്ട്",
            "Find my car" to "എന്റെ കാർ കണ്ടെത്തുക",
            "Showrooms near me" to "സമീപത്തുള്ള ഷോറൂമുകൾ",
            "Compare" to "താരതമ്യം ചെയ്യുക",
            "Cars" to "കാറുകൾ",
            "Bikes" to "ബൈക്കുകൾ"
        ),
        "mr" to mapOf(
            "Home" to "मुख्यपृष्ठ",
            "Explore" to "शोधा",
            "Offers" to "ऑफर्स",
            "Calculator" to "कॅल्क्युलेटर",
            "Profile" to "प्रोफाइल",
            "Preferences" to "पसंती",
            "Language" to "भाषा",
            "Appearance" to "दिसणे",
            "City for prices" to "किंमतींसाठी शहर",
            "Buying guide" to "खरेदी मार्गदर्शक",
            "Saved cars" to "जतन केलेल्या कार",
            "Sign in or create account" to "साइन इन करा किंवा खाते उघडा",
            "Sign out" to "साइन आउट",
            "Find my car" to "माझी कार शोधा",
            "Showrooms near me" to "जवळचे शोरूम",
            "Compare" to "तुलना करा",
            "Cars" to "गाड्या",
            "Bikes" to "बाईक्स"
        ),
        "bn" to mapOf(
            "Home" to "হোম",
            "Explore" to "অন্বেষণ করুন",
            "Offers" to "অফার",
            "Calculator" to "ক্যালকুলেটর",
            "Profile" to "প্রোফাইল",
            "Preferences" to "পছন্দসমূহ",
            "Language" to "ভাষা",
            "City for prices" to "দামের জন্য শহর",
            "Buying guide" to "ক্রয় নির্দেশিকা",
            "Saved cars" to "সংরক্ষিত গাড়ি",
            "Sign in or create account" to "সাইন ইন বা অ্যাকাউন্ট তৈরি করুন",
            "Find my car" to "আমার গাড়ি খুঁজুন",
            "Showrooms near me" to "কাছাকাছি শোরুম",
            "Compare" to "তুলনা করুন",
            "Cars" to "গাড়ি",
            "Bikes" to "বাইক"
        ),
        "gu" to mapOf(
            "Home" to "હોમ",
            "Explore" to "શોધો",
            "Offers" to "ઑફર્સ",
            "Calculator" to "કેલ્ક્યુલેટર",
            "Profile" to "પ્રોફાઇલ",
            "Preferences" to "પસંદગીઓ",
            "Language" to "ભાષા",
            "City for prices" to "કિંમતો માટે શહેર",
            "Buying guide" to "ખરીદી માર્ગદર્શિકા",
            "Saved cars" to "સાચવેલી કારો",
            "Sign in or create account" to "સાઇન ઇન કરો અથવા એકાઉન્ટ બનાવો",
            "Find my car" to "મારી કાર શોધો",
            "Showrooms near me" to "નજીકના શોરૂમ",
            "Compare" to "સરખામણી કરો",
            "Cars" to "કારો",
            "Bikes" to "બાઇક્સ"
        ),
        "pa" to mapOf(
            "Home" to "ਮੁੱਖ ਪੰਨਾ",
            "Explore" to "ਐਕਸਪਲੋਰ ਕਰੋ",
            "Offers" to "ਆਫਰਾਂ",
            "Calculator" to "ਕੈਲਕੂਲੇਟਰ",
            "Profile" to "ਪ੍ਰੋਫਾਈਲ",
            "Preferences" to "ਤਰਜੀਹਾਂ",
            "Language" to "ਭਾਸ਼ਾ",
            "City for prices" to "ਕੀਮਤਾਂ ਲਈ ਸ਼ਹਿਰ",
            "Buying guide" to "ਖਰੀਦਣ ਲਈ ਗਾਈਡ",
            "Saved cars" to "ਸੰਭਾਲੀਆਂ ਕਾਰਾਂ",
            "Sign in or create account" to "ਸਾਈਨ ਇਨ ਕਰੋ ਜਾਂ ਖਾਤਾ ਬਣਾਓ",
            "Find my car" to "ਮੇਰੀ ਕਾਰ ਲੱਭੋ",
            "Showrooms near me" to "ਨੇੜਲੇ ਸ਼ੋਰੂਮ",
            "Compare" to "ਤੁਲਨਾ ਕਰੋ",
            "Cars" to "ਕਾਰਾਂ",
            "Bikes" to "ਬਾਈਕਾਂ"
        ),
        "es" to mapOf(
            "Home" to "Inicio",
            "Explore" to "Explorar",
            "Offers" to "Ofertas",
            "Calculator" to "Calculadora",
            "Profile" to "Perfil",
            "Preferences" to "Preferencias",
            "Language" to "Idioma",
            "Appearance" to "Apariencia",
            "City for prices" to "Ciudad para precios",
            "Buying guide" to "Guía de compra",
            "Saved cars" to "Coches guardados",
            "Sign in or create account" to "Iniciar sesión o crear cuenta",
            "Sign out" to "Cerrar sesión",
            "Find my car" to "Encontrar mi coche",
            "Showrooms near me" to "Concesionarios cercanos",
            "Compare" to "Comparar",
            "Cars" to "Coches",
            "Bikes" to "Motos",
            "See all" to "Ver todo"
        ),
        "fr" to mapOf(
            "Home" to "Accueil",
            "Explore" to "Explorer",
            "Offers" to "Offres",
            "Calculator" to "Calculatrice",
            "Profile" to "Profil",
            "Preferences" to "Préférences",
            "Language" to "Langue",
            "Appearance" to "Apparence",
            "City for prices" to "Ville pour les prix",
            "Buying guide" to "Guide d'achat",
            "Saved cars" to "Voitures enregistrées",
            "Sign in or create account" to "Se connecter ou s'inscrire",
            "Sign out" to "Se déconnecter",
            "Find my car" to "Trouver ma voiture",
            "Showrooms near me" to "Concessionnaires proches",
            "Compare" to "Comparer",
            "Cars" to "Voitures",
            "Bikes" to "Motos",
            "See all" to "Voir tout"
        ),
        "de" to mapOf(
            "Home" to "Startseite",
            "Explore" to "Entdecken",
            "Offers" to "Angebote",
            "Calculator" to "Rechner",
            "Profile" to "Profil",
            "Preferences" to "Einstellungen",
            "Language" to "Sprache",
            "Appearance" to "Erscheinungsbild",
            "City for prices" to "Stadt für Preise",
            "Buying guide" to "Kaufberater",
            "Saved cars" to "Gespeicherte Autos",
            "Sign in or create account" to "Anmelden oder Registrieren",
            "Sign out" to "Abmelden",
            "Find my car" to "Mein Auto finden",
            "Showrooms near me" to "Autohäuser in der Nähe",
            "Compare" to "Vergleichen",
            "Cars" to "Autos",
            "Bikes" to "Motorräder",
            "See all" to "Alle anzeigen"
        ),
        "ar" to mapOf(
            "Home" to "الرئيسية",
            "Explore" to "استكشف",
            "Offers" to "عروض",
            "Calculator" to "حاسبة",
            "Profile" to "الملف الشخصي",
            "Preferences" to "التفضيلات",
            "Language" to "اللغة",
            "Appearance" to "المظهر",
            "City for prices" to "مدينة الأسعار",
            "Buying guide" to "دليل الشراء",
            "Saved cars" to "السيارات المحفوظة",
            "Sign in or create account" to "تسجيل الدخول أو إنشاء حساب",
            "Sign out" to "تسجيل الخروج",
            "Find my car" to "ابحث عن سيارتي",
            "Showrooms near me" to "صالات العرض القريبة",
            "Compare" to "مقارنة",
            "Cars" to "سيارات",
            "Bikes" to "دراجات نارية",
            "See all" to "عرض الكل"
        )
    )
}

@Composable
fun t(key: String): String {
    val lang by AppLanguage.currentLanguage.collectAsState()
    return AppLanguage.translate(key, lang)
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LanguagePickerDialog(onDismiss: () -> Unit) {
    val current by AppLanguage.currentLanguage.collectAsState()
    BasicAlertDialog(onDismissRequest = onDismiss) {
        Surface(
            shape = MaterialTheme.shapes.extraLarge,
            color = Panel,
            tonalElevation = 6.dp,
            modifier = Modifier.fillMaxWidth().padding(16.dp)
        ) {
            Column(Modifier.padding(20.dp)) {
                Row(
                    Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Column {
                        Text(
                            text = t("Language"),
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = "Choose your language / भाषा चुनें",
                            style = MaterialTheme.typography.bodySmall,
                            color = Mute
                        )
                    }
                    IconButton(onClick = onDismiss) {
                        Icon(Icons.Outlined.Close, contentDescription = "Close", tint = Mute)
                    }
                }
                Spacer(Modifier.padding(top = 12.dp))
                LazyColumn(
                    modifier = Modifier.heightIn(max = 380.dp),
                    verticalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    items(AppLanguage.languages, key = { it.code }) { lang ->
                        val selected = lang.code == current
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(Corner)
                                .background(if (selected) Ignition.copy(alpha = 0.12f) else Color.Transparent)
                                .clickable {
                                    AppLanguage.set(lang.code)
                                    onDismiss()
                                }
                                .padding(horizontal = 14.dp, vertical = 12.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(text = lang.flag, style = MaterialTheme.typography.titleMedium)
                            Spacer(Modifier.width(12.dp))
                            Column(Modifier.weight(1f)) {
                                Text(
                                    text = lang.nativeName,
                                    style = MaterialTheme.typography.bodyLarge,
                                    fontWeight = if (selected) FontWeight.Bold else FontWeight.Medium,
                                    color = if (selected) Ignition else Ink
                                )
                                Text(
                                    text = lang.name,
                                    style = MaterialTheme.typography.bodySmall,
                                    color = Mute
                                )
                            }
                            if (selected) {
                                Box(
                                    Modifier
                                        .size(24.dp)
                                        .clip(CircleShape)
                                        .background(Ignition),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Icon(
                                        Icons.Outlined.Check,
                                        contentDescription = null,
                                        tint = Color.White,
                                        modifier = Modifier.size(16.dp)
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
