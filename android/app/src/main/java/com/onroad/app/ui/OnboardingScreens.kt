package com.onroad.app.ui

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.core.animateDpAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.automirrored.outlined.Logout
import androidx.compose.material.icons.outlined.CurrencyRupee
import androidx.compose.material.icons.outlined.Dns
import androidx.compose.material.icons.outlined.LocationOn
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.ReceiptLong
import androidx.compose.material.icons.outlined.Storefront
import androidx.compose.material.icons.outlined.Visibility
import androidx.compose.material.icons.outlined.VisibilityOff
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.onroad.app.data.LoginIn
import com.onroad.app.data.SignupIn
import kotlinx.coroutines.async
import kotlinx.coroutines.launch
import retrofit2.HttpException

private data class Slide(val icon: ImageVector, val tint: Color, val title: String, val body: String)

private val SLIDES = listOf(
    Slide(Icons.Outlined.CurrencyRupee, Ignition, "The real price,\nnot the brochure one",
        "Every car and bike sold in India, with the manufacturer's own ex-showroom price for your city."),
    Slide(Icons.Outlined.ReceiptLong, Electric, "Every rupee\nexplained",
        "Road tax, registration, insurance and cess from your state's official rules. Dealer padding gets flagged."),
    Slide(Icons.Outlined.Storefront, Good, "Showrooms\nnear you",
        "Official dealers by distance from where you are, with what buyers say about them."),
)

/** First-run welcome: three slides, then the city, then optional sign-in. */
@Composable
fun WelcomeScreen(onCity: () -> Unit, onDone: (signIn: Boolean) -> Unit, vm: BrowseVM = hiltViewModel()) {
    val pager = rememberPagerState { SLIDES.size }
    val scope = rememberCoroutineScope()
    val city by vm.prefs.city.collectAsStateWithLifecycle()
    val last = pager.currentPage == SLIDES.lastIndex
    var locMsg by remember { mutableStateOf<String?>(null) }
    // the city list loads while this screen is open, so picking the nearest city is instant
    val citiesAhead = remember { scope.async { runCatching { vm.api.cities() }.getOrElse { emptyList() } } }
    val locate = com.onroad.app.data.rememberLocator(vm.prefs) { loc, problem ->
        scope.launch {
            if (loc == null) { locMsg = (problem ?: com.onroad.app.data.LocationProblem.NoFix).message; return@launch }
            locMsg = "Got your location. Finding your city…"
            var cities = citiesAhead.await()                        // fetched while the phone was locating
            for (i in 0 until 3) {                                  // the server may be waking up: keep trying briefly
                if (cities.isNotEmpty()) break
                kotlinx.coroutines.delay(4000)
                cities = runCatching { vm.api.cities() }.getOrElse { emptyList() }
            }
            val near = cities.minByOrNull { com.onroad.app.data.kmBetween(loc.latitude, loc.longitude, it.lat, it.lng) }
            locMsg = if (near != null) { vm.prefs.setCity(near.name); "You're near ${near.name}. Showrooms are sorted by distance from you." }
                     else "Location saved. We'll pick your city as soon as OnRoad connects."
        }
    }
    Column(Modifier.fillMaxSize().background(Night).statusBarsPadding().navigationBarsPadding().padding(24.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("on", style = MaterialTheme.typography.titleLarge); Text("road", style = MaterialTheme.typography.titleLarge, color = Ignition)
            Spacer(Modifier.weight(1f))
            TextButton(onClick = { vm.prefs.onboarded = true; onDone(false) }) { Text("Skip", color = Mute) }
        }
        HorizontalPager(pager, Modifier.weight(1f)) { i ->
            val sl = SLIDES[i]
            Column(Modifier.fillMaxSize(), verticalArrangement = Arrangement.Center) {
                OnboardingArt(listOf("price", "receipt", "showrooms")[i])
                Spacer(Modifier.height(24.dp))
                Text(sl.title, style = MaterialTheme.typography.displaySmall)
                Spacer(Modifier.height(14.dp))
                Text(sl.body, color = Mute, style = MaterialTheme.typography.bodyLarge)
            }
        }
        Row(Modifier.fillMaxWidth().padding(vertical = 18.dp), horizontalArrangement = Arrangement.Center) {
            repeat(SLIDES.size) { i ->
                val w by animateDpAsState(if (pager.currentPage == i) 26.dp else 8.dp, label = "dot")
                Box(Modifier.padding(horizontal = 4.dp).height(8.dp).width(w).clip(CircleShape).background(if (pager.currentPage == i) Ignition else Line))
            }
        }
        AnimatedContent(last, label = "cta") { isLast ->
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                if (isLast) {
                    Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(Panel2).clickable(onClick = onCity).padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Outlined.LocationOn, null, tint = Ignition); Spacer(Modifier.width(10.dp))
                        Column(Modifier.weight(1f)) { Text("Prices for", color = Mute, style = MaterialTheme.typography.labelSmall); Text(city, fontWeight = FontWeight.SemiBold) }
                        Text("Change", color = Ignition)
                    }
                    OutlinedButton(onClick = { locMsg = "Finding you…"; locate() }, Modifier.fillMaxWidth().height(50.dp)) {
                        Icon(Icons.Outlined.LocationOn, null, tint = Ignition); Spacer(Modifier.width(8.dp)); Text("Use my location", color = Ink)
                    }
                    locMsg?.let { Text(it, color = Mute, style = MaterialTheme.typography.bodySmall) }
                    Button(onClick = { vm.prefs.onboarded = true; onDone(true) }, Modifier.fillMaxWidth().height(54.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = Ignition)) { Text("Create account or sign in", fontWeight = FontWeight.SemiBold) }
                    OutlinedButton(onClick = { vm.prefs.onboarded = true; onDone(false) }, Modifier.fillMaxWidth().height(54.dp)) { Text("Browse without an account", color = Ink) }
                } else {
                    Button(onClick = { scope.launch { pager.animateScrollToPage(pager.currentPage + 1) } }, Modifier.fillMaxWidth().height(54.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = Ignition)) { Text("Next", fontWeight = FontWeight.SemiBold) }
                }
            }
        }
    }
}

/** Sign in / create account against the same OnRoad accounts as the website. */
@Composable
fun AuthScreen(onBack: () -> Unit, onDone: () -> Unit, vm: BrowseVM = hiltViewModel()) {
    var signup by remember { mutableStateOf(false) }
    var name by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var phone by remember { mutableStateOf("") }
    var pw by remember { mutableStateOf("") }
    var show by remember { mutableStateOf(false) }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    fun submit() {
        error = when {
            signup && name.isBlank() -> "Enter your name"
            !email.contains('@') -> "Enter a valid email"
            pw.length < 8 -> "Password needs at least 8 characters"
            else -> null
        }
        if (error != null) return
        busy = true
        scope.launch {
            runCatching {
                if (signup) vm.api.signup(SignupIn(name.trim(), email.trim(), phone.trim().ifBlank { null }, pw))
                else vm.api.login(LoginIn(email.trim(), pw))
            }.onSuccess { vm.prefs.setAccount(it); onDone() }
                .onFailure { e ->
                    error = when ((e as? HttpException)?.code()) {
                        401 -> "Email or password is wrong"
                        409 -> "An account with this email already exists. Sign in instead."
                        429 -> "Too many attempts. Try again in a few minutes."
                        null -> "Can't reach OnRoad. Check your connection."
                        else -> "Something went wrong. Please try again."
                    }
                }
            busy = false
        }
    }

    val ctx = androidx.compose.ui.platform.LocalContext.current
    // Sign in with Google (Credential Manager): Google returns an ID token for our web client, the server verifies it
    fun google() {
        busy = true; error = null
        scope.launch {
            runCatching {
                val clientId = vm.api.googleConfig().clientId ?: error("Google sign-in isn't set up on the server")
                val option = com.google.android.libraries.identity.googleid.GetSignInWithGoogleOption.Builder(clientId).build()
                val req = androidx.credentials.GetCredentialRequest.Builder().addCredentialOption(option).build()
                val cred = androidx.credentials.CredentialManager.create(ctx).getCredential(ctx, req).credential
                val token = com.google.android.libraries.identity.googleid.GoogleIdTokenCredential.createFrom(cred.data).idToken
                vm.api.google(com.onroad.app.data.GoogleIn(token))
            }.onSuccess { vm.prefs.setAccount(it); onDone() }
                .onFailure { e ->
                    error = when (e) {
                        is androidx.credentials.exceptions.GetCredentialCancellationException -> null
                        is androidx.credentials.exceptions.NoCredentialException -> "Add a Google account to this phone to sign in with Google."
                        is androidx.credentials.exceptions.GetCredentialException -> "Google sign-in isn't available right now. Use email instead."
                        is HttpException -> if (e.code() == 401) "Google sign-in couldn't be verified. Try again." else "Something went wrong. Please try again."
                        else -> e.message ?: "Can't reach OnRoad. Check your connection."
                    }
                }
            busy = false
        }
    }

    Column(Modifier.fillMaxSize().background(Night).verticalScroll(rememberScrollState()).statusBarsPadding().navigationBarsPadding().imePadding()) {
        IconButton(onBack, Modifier.padding(4.dp)) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "Back") }
        Column(Modifier.padding(horizontal = 24.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Text(if (signup) "Create your account" else "Welcome back", style = MaterialTheme.typography.displaySmall)
            Text(if (signup) "Save cars, get dealer quotes and rate the showroom you bought from." else "Sign in to see your saved cars and quotes.", color = Mute)
            Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(50)).background(Panel2).padding(4.dp)) {
                listOf(false to "Sign in", true to "Create account").forEach { (k, l) ->
                    Text(l, textAlign = TextAlign.Center, fontWeight = FontWeight.SemiBold, color = if (signup == k) Color.White else Mute,
                        modifier = Modifier.weight(1f).clip(RoundedCornerShape(50)).background(if (signup == k) Ignition else Color.Transparent)
                            .clickable { signup = k; error = null }.padding(vertical = 10.dp))
                }
            }
            androidx.compose.material3.OutlinedButton(::google, Modifier.fillMaxWidth().height(54.dp), enabled = !busy,
                border = androidx.compose.foundation.BorderStroke(1.dp, Line)) {
                Text("G", color = Color(0xFF4285F4), fontWeight = FontWeight.Black, style = MaterialTheme.typography.titleMedium)
                androidx.compose.foundation.layout.Spacer(Modifier.width(10.dp))
                Text("Continue with Google", color = Ink, fontWeight = FontWeight.SemiBold)
            }
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.weight(1f).height(1.dp).background(Line)); Text("  or with email  ", color = Mute, style = MaterialTheme.typography.bodySmall)
                Box(Modifier.weight(1f).height(1.dp).background(Line))
            }
            if (signup) OutlinedTextField(name, { name = it.take(80) }, Modifier.fillMaxWidth(), label = { Text("Full name") }, singleLine = true)
            OutlinedTextField(email, { email = it.take(120) }, Modifier.fillMaxWidth(), label = { Text("Email") }, singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email))
            if (signup) OutlinedTextField(phone, { phone = it.filter { c -> c.isDigit() || c == '+' }.take(14) }, Modifier.fillMaxWidth(),
                label = { Text("Mobile (optional)") }, singleLine = true, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone))
            OutlinedTextField(pw, { pw = it.take(200) }, Modifier.fillMaxWidth(), label = { Text("Password") }, singleLine = true,
                visualTransformation = if (show) VisualTransformation.None else PasswordVisualTransformation(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                trailingIcon = { IconButton({ show = !show }) { Icon(if (show) Icons.Outlined.VisibilityOff else Icons.Outlined.Visibility, if (show) "Hide" else "Show") } })
            error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            Button(::submit, Modifier.fillMaxWidth().height(54.dp), enabled = !busy, colors = ButtonDefaults.buttonColors(containerColor = Ignition)) {
                Text(if (busy) "Please wait…" else if (signup) "Create account" else "Sign in", fontWeight = FontWeight.SemiBold)
            }
            TextButton(onClick = onDone, Modifier.align(Alignment.CenterHorizontally)) { Text("Not now", color = Mute) }
        }
    }
}

/** Account: who is signed in, sign out, and the server address (for testing against a local API). */
@Composable
fun AccountScreen(onBack: () -> Unit, onSignIn: () -> Unit, vm: BrowseVM = hiltViewModel()) {
    val acc by vm.prefs.account.collectAsStateWithLifecycle()
    val scope = rememberCoroutineScope()
    var server by remember { mutableStateOf(vm.prefs.server()) }
    LaunchedEffect(Unit) { if (vm.prefs.session != null) runCatching { vm.api.me() }.onSuccess { vm.prefs.setAccount(it) }.onFailure { vm.prefs.setAccount(null) } }
    Column(Modifier.fillMaxSize().background(Night).verticalScroll(rememberScrollState()).statusBarsPadding().navigationBarsPadding().imePadding()) {
        Row(Modifier.padding(4.dp), verticalAlignment = Alignment.CenterVertically) {
            IconButton(onBack) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "Back") }
            Text("My garage", style = MaterialTheme.typography.titleLarge)
        }
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Tile(Modifier.fillMaxWidth()) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(Modifier.size(52.dp).clip(CircleShape).background(Ignition), contentAlignment = Alignment.Center) {
                        val a = acc
                        if (a != null && a.name.isNotBlank()) Text(a.name.take(1).uppercase(), style = MaterialTheme.typography.titleLarge, color = Color.White)
                        else Icon(Icons.Outlined.Person, null, tint = Color.White)
                    }
                    Spacer(Modifier.width(14.dp))
                    Column(Modifier.weight(1f)) {
                        Text(acc?.name ?: "Not signed in", style = MaterialTheme.typography.titleMedium)
                        Text(acc?.email ?: "Sign in to save cars and get dealer quotes", color = Mute, style = MaterialTheme.typography.bodyMedium)
                    }
                }
            }
            if (acc == null) Button(onSignIn, Modifier.fillMaxWidth().height(52.dp), colors = ButtonDefaults.buttonColors(containerColor = Ignition)) { Text("Sign in or create account") }
            else OutlinedButton(onClick = { scope.launch { runCatching { vm.api.logout() }; vm.prefs.session = null; vm.prefs.setAccount(null) } },
                Modifier.fillMaxWidth().height(52.dp)) { Icon(Icons.AutoMirrored.Outlined.Logout, null); Spacer(Modifier.width(8.dp)); Text("Sign out", color = Ink) }
            Tile(Modifier.fillMaxWidth()) {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) { Icon(Icons.Outlined.Dns, null, tint = Mute); Spacer(Modifier.width(8.dp)); Text("Server", fontWeight = FontWeight.SemiBold) }
                    OutlinedTextField(server, { server = it }, Modifier.fillMaxWidth(), singleLine = true, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri))
                    TextButton(onClick = { vm.prefs.setServer(if (server.startsWith("http")) server else "http://$server") }) { Text("Save", color = Ignition) }
                }
            }
            Text("Prices are the manufacturers' own; taxes follow each state's official rules.", color = Mute, style = MaterialTheme.typography.bodyMedium)
        }
    }
}


/** A character illustration for an onboarding slide (unDraw, recoloured to the OnRoad orange; assets/onboarding),
 *  on a white card so its dark details stay visible in dark mode too. */
@Composable
private fun OnboardingArt(name: String) = Box(
    Modifier.fillMaxWidth().aspectRatio(1.25f).clip(RoundedCornerShape(24.dp)).background(Color.White).padding(22.dp),
    contentAlignment = Alignment.Center,
) {
    val ctx = androidx.compose.ui.platform.LocalContext.current
    val generated = "onb-$name".replace("onb-showrooms", "onb-showrooms")
    val url = if (hasArt(ctx, generated)) "file:///android_asset/illustrations/$generated.webp" else "file:///android_asset/onboarding/$name.svg"
    coil3.compose.AsyncImage(url, null, contentScale = androidx.compose.ui.layout.ContentScale.Fit, modifier = Modifier.fillMaxSize())
}
