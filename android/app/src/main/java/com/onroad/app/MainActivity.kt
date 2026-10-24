package com.onroad.app

import android.annotation.SuppressLint
import android.app.Application
import android.graphics.Color
import android.location.LocationManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.ui.Modifier
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import coil3.ImageLoader
import coil3.SingletonImageLoader
import coil3.svg.SvgDecoder
import coil3.request.crossfade
import com.onroad.app.data.City
import androidx.compose.runtime.remember
import com.onroad.app.data.Prefs
import com.onroad.app.ui.AccountScreen
import com.onroad.app.ui.AuthScreen
import com.onroad.app.ui.WelcomeScreen
import javax.inject.Inject
import androidx.compose.foundation.layout.Column
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Calculate
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Text
import androidx.compose.ui.unit.dp
import androidx.navigation.compose.currentBackStackEntryAsState
import com.onroad.app.ui.Ignition
import com.onroad.app.ui.Mute
import com.onroad.app.ui.Panel
import com.onroad.app.ui.BrandScreen
import com.onroad.app.ui.FinderScreen
import com.onroad.app.ui.ExploreScreen
import com.onroad.app.ui.GuideScreen
import com.onroad.app.ui.ProfileScreen
import androidx.compose.material.icons.outlined.Explore
import androidx.compose.material.icons.outlined.LocalOffer
import com.onroad.app.ui.OffersScreen
import com.onroad.app.ui.CalculatorScreen
import com.onroad.app.ui.CityScreen
import com.onroad.app.ui.HomeScreen
import com.onroad.app.ui.ModelScreen
import com.onroad.app.ui.Night
import com.onroad.app.ui.OnRoadTheme
import com.onroad.app.ui.SearchScreen
import dagger.hilt.android.AndroidEntryPoint
import dagger.hilt.android.HiltAndroidApp
import java.net.URLDecoder
import java.net.URLEncoder

@HiltAndroidApp
class OnRoadApp : Application(), SingletonImageLoader.Factory {
    override fun newImageLoader(context: coil3.PlatformContext) =
        ImageLoader.Builder(context).components { add(SvgDecoder.Factory()) }.crossfade(true).build()   // brand logos are SVG

    override fun onCreate() { super.onCreate(); com.onroad.app.data.AlertWorker.schedule(this) }
}

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    @Inject lateinit var prefs: Prefs
    private val askNotify = registerForActivityResult(ActivityResultContracts.RequestPermission()) { }
    private val askLocation = registerForActivityResult(ActivityResultContracts.RequestPermission()) { }

    /** Nearest supported city from the phone's last known coarse location (no GPS fix, no Play Services needed). */
    @SuppressLint("MissingPermission")
    private fun nearest(cities: List<City>): City? {
        askLocation.launch(android.Manifest.permission.ACCESS_COARSE_LOCATION)
        val lm = getSystemService(LocationManager::class.java)
        val loc = runCatching { lm.getProviders(true).mapNotNull { lm.getLastKnownLocation(it) }.maxByOrNull { it.time } }.getOrNull() ?: return null
        prefs.lat = loc.latitude; prefs.lng = loc.longitude
        return cities.minByOrNull { (it.lat - loc.latitude) * (it.lat - loc.latitude) + (it.lng - loc.longitude) * (it.lng - loc.longitude) }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        super.onCreate(savedInstanceState)
        enableEdgeToEdge(SystemBarStyle.dark(Color.TRANSPARENT), SystemBarStyle.dark(Color.TRANSPARENT))
        setContent {
            OnRoadTheme {
                val nav = rememberNavController()
                val enc = { s: String -> URLEncoder.encode(s, "UTF-8") }
                val start = remember { if (prefs.onboarded) "home" else "welcome" }
                val route = nav.currentBackStackEntryAsState().value?.destination?.route
                androidx.compose.runtime.LaunchedEffect(route) {
                    if (route == "home" && android.os.Build.VERSION.SDK_INT >= 33 && !prefs.askedNotify) {
                        prefs.askedNotify = true
                        kotlinx.coroutines.delay(1500)            // let Home render first
                        askNotify.launch(android.Manifest.permission.POST_NOTIFICATIONS)
                    }
                }
                // opened from an alert: jump to that screen once the app is past onboarding
                androidx.compose.runtime.LaunchedEffect(Unit) {
                    intent?.getStringExtra("route")?.let { r -> if (prefs.onboarded) nav.navigate(if (r.startsWith("model/")) "model/${enc(r.removePrefix("model/"))}" else r) }
                }
                val tabs = listOf(Triple("home", "Home", Icons.Outlined.Home), Triple("explore", "Explore", Icons.Outlined.Explore),
                    Triple("offers", "Offers", Icons.Outlined.LocalOffer), Triple("calc", "Calculator", Icons.Outlined.Calculate),
                    Triple("account", "Profile", Icons.Outlined.Person))
                Column(Modifier.fillMaxSize().background(Night).statusBarsPadding()) {
                NavHost(nav, start, Modifier.weight(1f)) {
                    composable("welcome") {
                        WelcomeScreen(onCity = { nav.navigate("city") }, onDone = { signIn ->
                            nav.navigate("home") { popUpTo("welcome") { inclusive = true } }
                            if (signIn) nav.navigate("auth")
                        })
                    }
                    composable("auth") { AuthScreen(onBack = { nav.popBackStack() }, onDone = { nav.popBackStack() }) }
                    composable("account") { ProfileScreen(onSignIn = { nav.navigate("auth") }, onModel = { nav.navigate("model/${enc(it)}") },
                        onCity = { nav.navigate("city") }, onGuide = { nav.navigate("guide") }, onShowrooms = { nav.navigate("showrooms") },
                        onOffers = { nav.navigate("offers") }, onFinder = { nav.navigate("finder") }, onCalc = { nav.navigate("calc") }) }
                    composable("explore") { ExploreScreen(onModel = { nav.navigate("model/${enc(it)}") }, onSearch = { nav.navigate("search") }) }
                    composable("explore-budget/{type}/{budget}") { e ->
                        ExploreScreen(onModel = { nav.navigate("model/${enc(it)}") }, onSearch = { nav.navigate("search") },
                            initType = e.arguments?.getString("type") ?: "car", initBudget = e.arguments?.getString("budget"))
                    }
                    composable("compare") { com.onroad.app.ui.CompareScreen(onBack = { nav.popBackStack() }, onModel = { nav.navigate("model/${enc(it)}") }) }
                    composable("guide") { GuideScreen(onBack = { nav.popBackStack() }) }
                    composable("home") {
                        HomeScreen(onBrand = { nav.navigate("brand/${it.slug}/${enc(it.name)}") }, onModel = { nav.navigate("model/${enc(it)}") },
                            onSearch = { nav.navigate("search") }, onCity = { nav.navigate("city") }, onCalc = { nav.navigate("calc") }, onAccount = { nav.navigate("account") },
                            onOffers = { nav.navigate("offers") }, onFinder = { nav.navigate("finder") }, onShowrooms = { nav.navigate("showrooms") },
                            onCompare = { nav.navigate("compare") }, onGuide = { nav.navigate("guide") },
                            onBudget = { t, b -> nav.navigate("explore-budget/$t/$b") })
                    }
                    composable("brand/{slug}/{name}") { e ->
                        BrandScreen(e.arguments!!.getString("slug")!!, URLDecoder.decode(e.arguments!!.getString("name")!!, "UTF-8"),
                            onModel = { nav.navigate("model/${enc(it)}") }, onBack = { nav.popBackStack() })
                    }
                    composable("model/{id}") { e -> ModelScreen(URLDecoder.decode(e.arguments!!.getString("id")!!, "UTF-8"), onBack = { nav.popBackStack() }, onSignIn = { nav.navigate("auth") }) }
                    composable("offers") { OffersScreen(onBack = { nav.popBackStack() }) }
                    composable("finder") { FinderScreen(onBack = { nav.popBackStack() }, onModel = { nav.navigate("model/${enc(it)}") }) }
                    composable("search") { SearchScreen(onModel = { nav.navigate("model/${enc(it)}") }, onBack = { nav.popBackStack() }) }
                    composable("calc") { CalculatorScreen(onBack = { nav.popBackStack() }) }
                    composable("city") { CityScreen(onBack = { nav.popBackStack() }) }
                    composable("showrooms") { com.onroad.app.ui.ShowroomsScreen(onBack = { nav.popBackStack() }) }
                }
                // Cars24 / ACKO-style persistent tab bar on the top-level screens
                if (route in tabs.map { it.first }) NavigationBar(containerColor = Panel, tonalElevation = 0.dp) {
                    tabs.forEach { (r, label, icon) ->
                        NavigationBarItem(selected = route == r, label = { Text(label) }, icon = { Icon(icon, label) },
                            colors = NavigationBarItemDefaults.colors(selectedIconColor = Ignition, selectedTextColor = Ignition,
                                indicatorColor = Ignition.copy(alpha = 0.14f), unselectedIconColor = Mute, unselectedTextColor = Mute),
                            onClick = { if (route != r) nav.navigate(r) { popUpTo("home") { saveState = true }; launchSingleTop = true; restoreState = true } })
                    }
                }
                }
            }
        }
    }
}
