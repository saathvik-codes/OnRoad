package com.onroad.app.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.outlined.StarOutline
import androidx.compose.material3.TextButton
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.layout.ContentScale
import coil3.compose.AsyncImage
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Call
import androidx.compose.material.icons.outlined.CloudOff
import androidx.compose.material.icons.outlined.Directions
import androidx.compose.material.icons.outlined.MyLocation
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import kotlinx.coroutines.launch
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.onroad.app.data.Brand
import com.onroad.app.data.NearDealer
import com.onroad.app.data.rememberLocator

/** Shown instead of an endless spinner when the server can't be reached. */
@Composable
fun ErrorState(message: String, onRetry: () -> Unit) = Column(
    Modifier.fillMaxWidth().padding(32.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(10.dp),
) {
    val ctx = androidx.compose.ui.platform.LocalContext.current
    if (hasArt(ctx, "error-offline")) Art("error-offline") else Icon(Icons.Outlined.CloudOff, null, tint = Mute, modifier = Modifier.size(40.dp))
    Text(message, color = Mute, textAlign = TextAlign.Center)
    Button(onRetry, colors = ButtonDefaults.buttonColors(containerColor = Panel2), shape = Corner) { Text("Try again", color = Ink) }
}

/** Nearest official showrooms of every brand (or the brands picked), with photo, ratings, call and directions. */
@Composable
fun ShowroomsScreen(onBack: () -> Unit, vm: BrowseVM = hiltViewModel()) {
    val ctx = LocalContext.current
    var type by remember { mutableStateOf("car") }
    var brand by remember { mutableStateOf<String?>(null) }
    var sort by remember { mutableStateOf("near") }
    var brands by remember { mutableStateOf<List<Brand>>(emptyList()) }
    var list by remember { mutableStateOf<List<NearDealer>?>(null) }
    var err by remember { mutableStateOf<String?>(null) }
    val cityNow by vm.prefs.city.collectAsStateWithLifecycle()
    var here by remember { mutableStateOf(vm.prefs.lat?.let { la -> vm.prefs.lng?.let { lo -> la to lo } }) }
    var fromGps by remember { mutableStateOf(false) }
    // picking another city moves the search there (its centre), so showrooms always match the chosen city
    LaunchedEffect(cityNow) { vm.prefs.lat?.let { la -> vm.prefs.lng?.let { lo -> if (here != la to lo) { here = la to lo; fromGps = false } } } }
    var tick by remember { mutableIntStateOf(0) }
    var rating by remember { mutableStateOf<NearDealer?>(null) }
    var reviews by remember { mutableStateOf<NearDealer?>(null) }
    var locOff by remember { mutableStateOf(false) }
    val locate = rememberLocator(vm.prefs) { loc, problem ->
        locOff = problem == com.onroad.app.data.LocationProblem.Off
        if (loc != null && (loc.latitude !in 6.0..37.5 || loc.longitude !in 68.0..97.5))
            err = "Your phone reports a location outside India, so there are no showrooms to show. Turn on precise location and try again."
        else if (loc != null) { here = loc.latitude to loc.longitude; fromGps = true }
        else err = (problem ?: com.onroad.app.data.LocationProblem.NoFix).message
    }
    LaunchedEffect(Unit) { if (here == null) locate() }
    LaunchedEffect(type, cityNow) {
        brands = runCatching { vm.api.brands(cityNow, type) }.getOrElse { emptyList() }.filter { it.models > 0 }.sortedByDescending { it.models }
    }
    LaunchedEffect(here, type, brand, tick) {
        val h = here ?: return@LaunchedEffect
        list = null; err = null
        runCatching { vm.api.dealersNear(h.first, h.second, brand, type) }
            .onSuccess { list = it }.onFailure { err = "Couldn't reach OnRoad. Check your connection." }
    }
    val shown = list?.let { l ->
        if (sort == "near") l else l.sortedWith(compareByDescending<NearDealer> { it.googleRating ?: it.rating ?: 0.0 }
            .thenByDescending { it.googleCount ?: it.ratingCount })
    }
    fun call(d: NearDealer) = d.phone?.let { ph -> ctx.startActivity(Intent(Intent.ACTION_DIAL, Uri.parse("tel:" + ph.split(',', '/', ';')[0].trim()))) }
    fun go(d: NearDealer) { if (d.lat != null && d.lng != null)
        ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://www.google.com/maps/dir/?api=1&destination=${d.lat},${d.lng}"))) }

    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 28.dp)) {
        item {
            ScreenHeader("Showrooms", "Official dealers of every brand", onBack)
            // where we're searching from
            Row(Modifier.padding(horizontal = 16.dp).fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(Panel)
                .border(1.dp, Line, RoundedCornerShape(16.dp)).clickable { here = null; locate() }.padding(horizontal = 14.dp, vertical = 12.dp),
                verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.size(34.dp).clip(CircleShape).background(Electric.copy(alpha = 0.15f)), contentAlignment = Alignment.Center) {
                    Icon(Icons.Outlined.MyLocation, null, tint = Electric, modifier = Modifier.size(18.dp))
                }
                Spacer(Modifier.width(12.dp))
                Column(Modifier.weight(1f)) {
                    Text(if (fromGps) "Near your location" else "Around $cityNow", fontWeight = FontWeight.SemiBold)
                    Text(if (fromGps) "Using your phone's location" else "Centre of $cityNow · tap to use your exact location", color = Mute,
                        style = MaterialTheme.typography.bodySmall)
                }
                Text("Locate", color = Ignition, style = MaterialTheme.typography.labelLarge)
            }
            Row(Modifier.padding(start = 16.dp, end = 16.dp, top = 14.dp), verticalAlignment = Alignment.CenterVertically) {
                Pills(listOf("car" to "Cars", "bike" to "Bikes"), type) { type = it; brand = null }
                Spacer(Modifier.weight(1f))
                Pills(listOf("near" to "Nearest", "rated" to "Top rated"), sort) { sort = it }
            }
            if (brands.isNotEmpty()) LazyRow(contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 14.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                items(brands, key = { it.slug }) { b ->
                    BrandLogo(b, brand == b.slug, vm.prefs.img(b.logo, 200)) { brand = if (brand == b.slug) null else b.slug }
                }
            }
        }
        val l = shown
        when {
            err != null -> item {
                Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
                    ErrorState(err!!) { err = null; if (here == null) locate() else tick++ }
                    if (locOff) Text("Open location settings", color = Ignition, style = MaterialTheme.typography.labelLarge,
                        modifier = Modifier.clickable { com.onroad.app.data.openLocationSettings(ctx) })
                }
            }
            here == null -> item {
                Column(Modifier.fillMaxWidth().padding(32.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    CircularProgressIndicator(color = Ignition); Text("Finding your location…", color = Mute)
                }
            }
            l == null -> item { Box(Modifier.fillMaxWidth().padding(40.dp), contentAlignment = Alignment.Center) { CircularProgressIndicator(color = Ignition) } }
            l.isEmpty() -> item {
                Column(Modifier.fillMaxWidth().padding(28.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                    Art("empty-showrooms")
                    Text("No listed showroom within about 300 km.", color = Mute)
                    if (brand != null) TextButton({ brand = null }) { Text("Show all brands", color = Ignition) }
                }
            }
            else -> {
                item {
                    Text("${l.size} showroom${if (l.size == 1) "" else "s"}${if (sort == "near") " · nearest first" else " · best rated first"}",
                        style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(start = 16.dp, top = 18.dp, bottom = 8.dp))
                }
                item(key = "hero-" + l.first().id) { FeaturedShowroom(l.first(), vm, ::call, ::go, { reviews = l.first() }) { rating = l.first() } }
                items(l.drop(1), key = { it.id }) { d -> ShowroomCard(d, vm, { call(d) }, { go(d) }, { reviews = d }) { rating = d } }
            }
        }
    }
    rating?.let { d -> RateSheet(d, vm) { posted -> rating = null; if (posted) tick++ } }
    reviews?.let { d -> ReviewsSheet(d, vm, onRate = { reviews = null; rating = d }) { reviews = null } }
}

/** Showroom photos are off for now (brand mark shown instead); set to true to bring them back. */
private const val SHOW_SHOWROOM_PHOTOS = false

@Composable
private fun ShowroomPhoto(d: NearDealer, vm: BrowseVM, modifier: Modifier, big: Boolean) = Box(
    modifier.clip(RoundedCornerShape(if (big) 20.dp else 14.dp))
        .background(Panel2), contentAlignment = Alignment.Center,
) {
    if (SHOW_SHOWROOM_PHOTOS && d.photoUrl != null) {
        AsyncImage(vm.prefs.img(d.photoUrl, if (big) 1000 else 400), d.name, contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize())
    } else {
        // no photo published: the brand's mark on a tinted tile, never a stock picture
        Box(Modifier.size(if (big) 86.dp else 46.dp).clip(RoundedCornerShape(if (big) 22.dp else 12.dp)).background(Color.White).padding(if (big) 14.dp else 7.dp)) {
            AsyncImage(vm.prefs.img("/api/logos/${d.brandSlug}", 200), d.brandName, contentScale = ContentScale.Fit, modifier = Modifier.fillMaxSize())
        }
    }
}

@Composable
private fun Ratings(d: NearDealer) = Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
    d.googleRating?.let { g ->
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("★ %.1f".format(g), color = Amber, fontWeight = FontWeight.Bold)
            Text(" Google${d.googleCount?.let { " (%,d)".format(it) } ?: ""}", color = Mute, style = MaterialTheme.typography.bodySmall)
        }
    }
    if (d.ratingCount > 0) Row(verticalAlignment = Alignment.CenterVertically) {
        Text("★ ${d.rating}", color = Good, fontWeight = FontWeight.Bold)
        Text(" ${d.ratingCount} OnRoad buyer${if (d.ratingCount > 1) "s" else ""}", color = Mute, style = MaterialTheme.typography.bodySmall)
    }
    if (d.googleRating == null && d.ratingCount == 0) Text("No ratings yet", color = Mute, style = MaterialTheme.typography.bodySmall)
    Text("Reviews ›", color = Ignition, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.SemiBold)
}

@Composable
private fun Action(icon: androidx.compose.ui.graphics.vector.ImageVector, label: String, tint: Color, modifier: Modifier, onClick: () -> Unit) = Row(
    modifier.clip(Corner).background(tint.copy(alpha = 0.12f)).clickable(onClick = onClick).padding(vertical = 10.dp),
    horizontalArrangement = Arrangement.Center, verticalAlignment = Alignment.CenterVertically,
) {
    Icon(icon, null, tint = tint, modifier = Modifier.size(17.dp)); Spacer(Modifier.width(6.dp))
    Text(label, color = tint, style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.SemiBold)
}

@Composable
private fun FeaturedShowroom(d: NearDealer, vm: BrowseVM, call: (NearDealer) -> Unit, go: (NearDealer) -> Unit, open: () -> Unit, rate: () -> Unit) =
    Tile(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 6.dp).clickable(onClick = open), pad = 12) {
        Column {
            Box {
                ShowroomPhoto(d, vm, Modifier.fillMaxWidth().aspectRatio(16 / 9f), big = true)
                Text("NEAREST", color = Color.White, style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(10.dp).clip(Corner).background(Ignition).padding(horizontal = 10.dp, vertical = 4.dp))
                d.distanceKm?.let { km ->
                    Text("%.1f km".format(km), color = Color.White, fontWeight = FontWeight.Bold,
                        modifier = Modifier.align(Alignment.TopEnd).padding(10.dp).clip(Corner).background(Color.Black.copy(alpha = 0.6f))
                            .padding(horizontal = 10.dp, vertical = 4.dp))
                }
            }
            d.photoCredit?.takeIf { SHOW_SHOWROOM_PHOTOS && d.photoUrl != null }?.let { Text(it, color = Mute, style = MaterialTheme.typography.labelSmall, modifier = Modifier.padding(top = 4.dp)) }
            Spacer(Modifier.height(10.dp))
            Chip(d.brandName, Ignition)
            Text(d.name, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold, maxLines = 2, overflow = TextOverflow.Ellipsis,
                modifier = Modifier.padding(top = 6.dp))
            Text(listOfNotNull(d.address.ifBlank { null }, d.city).joinToString(", "), color = Mute, style = MaterialTheme.typography.bodyMedium, maxLines = 2)
            Box(Modifier.padding(vertical = 10.dp)) { Ratings(d) }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                if (d.phone != null) Action(Icons.Outlined.Call, "Call", Good, Modifier.weight(1f)) { call(d) }
                if (d.lat != null) Action(Icons.Outlined.Directions, "Directions", Electric, Modifier.weight(1f)) { go(d) }
                Action(Icons.Outlined.StarOutline, "Rate", Amber, Modifier.weight(1f), rate)
            }
        }
    }

@Composable
private fun ShowroomCard(d: NearDealer, vm: BrowseVM, call: () -> Unit, go: () -> Unit, open: () -> Unit, rate: () -> Unit) =
    Tile(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 6.dp).clickable(onClick = open), pad = 12) {
        Column {
            Row {
                ShowroomPhoto(d, vm, Modifier.width(96.dp).height(84.dp), big = false)
                Spacer(Modifier.width(12.dp))
                Column(Modifier.weight(1f)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(d.brandName, color = Ignition, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.SemiBold,
                            maxLines = 1, modifier = Modifier.weight(1f))
                        d.distanceKm?.let { Text("%.1f km".format(it), color = Electric, style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.SemiBold) }
                    }
                    Text(d.name, style = MaterialTheme.typography.titleMedium, maxLines = 2, overflow = TextOverflow.Ellipsis)
                    Text(listOfNotNull(d.address.ifBlank { null }, d.city).joinToString(", "), color = Mute, style = MaterialTheme.typography.bodySmall, maxLines = 1,
                        overflow = TextOverflow.Ellipsis)
                    Box(Modifier.padding(top = 4.dp)) { Ratings(d) }
                }
            }
            Row(Modifier.padding(top = 10.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                if (d.phone != null) Action(Icons.Outlined.Call, "Call", Good, Modifier.weight(1f), call)
                if (d.lat != null) Action(Icons.Outlined.Directions, "Directions", Electric, Modifier.weight(1f), go)
                Action(Icons.Outlined.StarOutline, "Rate", Amber, Modifier.weight(1f), rate)
            }
        }
    }

/** A buyer rates the showroom they dealt with: overall stars, price honesty, add-on pressure, delivery. Needs sign-in. */
@OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)
@Composable
internal fun RateSheet(d: NearDealer, vm: BrowseVM, onDone: (Boolean) -> Unit) {
    val scope = androidx.compose.runtime.rememberCoroutineScope()
    val signedIn = vm.prefs.account.value != null || vm.prefs.session != null
    var stars by remember { mutableIntStateOf(0) }
    var honest by remember { mutableIntStateOf(0) }
    var noAddons by remember { mutableStateOf<Boolean?>(null) }
    var onTime by remember { mutableStateOf<Boolean?>(null) }
    var visit by remember { mutableStateOf("purchase") }
    var text by remember { mutableStateOf("") }
    var msg by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    @Composable fun starRow(v: Int, set: (Int) -> Unit) = Row {
        (1..5).forEach { n -> Text(if (n <= v) "★" else "☆", color = if (n <= v) Amber else Mute, style = MaterialTheme.typography.headlineSmall,
            modifier = Modifier.clickable { set(n) }.padding(horizontal = 3.dp)) }
    }
    @Composable fun yesNo(v: Boolean?, set: (Boolean) -> Unit) = Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        listOf(true to "Yes", false to "No").forEach { (b, l) -> Text(l, color = if (v == b) Color.White else Mute, style = MaterialTheme.typography.labelLarge,
            modifier = Modifier.clip(Corner).background(if (v == b) Ignition else Panel2).clickable { set(b) }.padding(horizontal = 14.dp, vertical = 7.dp)) }
    }
    androidx.compose.material3.ModalBottomSheet({ onDone(false) }, containerColor = Panel) {
        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 28.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("Rate ${d.name}", style = MaterialTheme.typography.titleLarge, maxLines = 2)
            if (!signedIn) { Text("Sign in from the Profile tab to rate a showroom. Ratings come only from OnRoad buyers.", color = Mute); return@Column }
            Row(verticalAlignment = Alignment.CenterVertically) { Text("Overall", Modifier.weight(1f)); starRow(stars) { stars = it } }
            Row(verticalAlignment = Alignment.CenterVertically) { Text("Final bill matched the quote", Modifier.weight(1f), color = Mute); starRow(honest) { honest = it } }
            Row(verticalAlignment = Alignment.CenterVertically) { Text("No forced add-ons or handling fees", Modifier.weight(1f), color = Mute); yesNo(noAddons) { noAddons = it } }
            Row(verticalAlignment = Alignment.CenterVertically) { Text("Delivered on the promised date", Modifier.weight(1f), color = Mute); yesNo(onTime) { onTime = it } }
            Pills(listOf("purchase" to "I bought here", "enquiry" to "Visited / quote", "service" to "Serviced here"), visit) { visit = it }
            androidx.compose.material3.OutlinedTextField(text, { text = it.take(1200) }, Modifier.fillMaxWidth(), minLines = 2,
                placeholder = { Text("What should other buyers know?") })
            msg?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            Button(onClick = {
                if (stars == 0) { msg = "Pick an overall rating"; return@Button }
                busy = true
                scope.launch {
                    runCatching { vm.api.rateDealer(com.onroad.app.data.DealerReviewIn(d.id, stars, honest.takeIf { it > 0 }, noAddons, onTime, visit, text)) }
                        .onSuccess { onDone(true) }.onFailure { msg = "Couldn't post your rating. Sign in again and retry." }
                    busy = false
                }
            }, Modifier.fillMaxWidth().height(50.dp), enabled = !busy, colors = ButtonDefaults.buttonColors(containerColor = Ignition), shape = Corner) {
                Text(if (busy) "Posting…" else "Post rating", fontWeight = FontWeight.SemiBold)
            }
        }
    }
}


/** Google's latest reviews (fetched live, never stored) and OnRoad buyers' own reviews of one showroom. */
@OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)
@Composable
private fun ReviewsSheet(d: NearDealer, vm: BrowseVM, onRate: () -> Unit, onClose: () -> Unit) {
    val ctx = LocalContext.current
    var data by remember { mutableStateOf<com.onroad.app.data.DealerReviews?>(null) }
    var failed by remember { mutableStateOf(false) }
    LaunchedEffect(d.id) { runCatching { vm.api.dealerReviews(d.id) }.onSuccess { data = it }.onFailure { failed = true } }
    val state = androidx.compose.material3.rememberModalBottomSheetState(skipPartiallyExpanded = true)
    androidx.compose.material3.ModalBottomSheet(onClose, sheetState = state, containerColor = Panel) {
        LazyColumn(Modifier.fillMaxWidth().fillMaxHeight(0.88f), contentPadding = PaddingValues(start = 20.dp, end = 20.dp, bottom = 28.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)) {
            item {
                Text(d.brandName, color = Ignition, style = MaterialTheme.typography.labelLarge)
                Text(d.name, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
                Text(listOfNotNull(d.address.ifBlank { null }, d.city).joinToString(", "), color = Mute, style = MaterialTheme.typography.bodySmall)
            }
            val res = data
            val g = res?.google
            when {
                failed -> item { Text("Couldn't load reviews. Check your connection.", color = Mute) }
                res == null -> item { Box(Modifier.fillMaxWidth().padding(30.dp), contentAlignment = Alignment.Center) { CircularProgressIndicator(color = Ignition) } }
                else -> {
                    item {
                        Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(Panel2).padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                            Column(Modifier.weight(1f)) {
                                Text("GOOGLE", style = MaterialTheme.typography.labelSmall, color = Mute)
                                if (g?.rating != null) Row(verticalAlignment = Alignment.Bottom) {
                                    Text("%.1f".format(g.rating), style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
                                    Text("  ★ · ${"%,d".format(g.count ?: 0)} reviews", color = Amber, modifier = Modifier.padding(bottom = 4.dp))
                                } else Text(g?.note ?: "Not on Google yet", color = Mute)
                            }
                            g?.mapsUri?.let { u -> Text("All on Maps ›", color = Electric, style = MaterialTheme.typography.labelLarge,
                                modifier = Modifier.clickable { ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(u))) }) }
                        }
                    }
                    items(g?.reviews.orEmpty()) { r -> ReviewItem(r.author ?: "Google user", r.rating, r.whenText, r.text, "Google") }
                    item {
                        Row(Modifier.fillMaxWidth().padding(top = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                            Column(Modifier.weight(1f)) {
                                Text("ONROAD BUYERS", style = MaterialTheme.typography.labelSmall, color = Mute)
                                Text(if (res.onroad.isEmpty()) "No OnRoad reviews yet" else "${res.onroad.size} review${if (res.onroad.size > 1) "s" else ""}",
                                    fontWeight = FontWeight.SemiBold)
                            }
                            Text("Write one", color = Ignition, style = MaterialTheme.typography.labelLarge, modifier = Modifier.clickable(onClick = onRate))
                        }
                    }
                    items(res.onroad) { r ->
                        Column {
                            ReviewItem(r.name ?: "Buyer", r.rating, r.created?.take(10), r.text.orEmpty(), when (r.visit) {
                                "purchase" -> "Bought here"; "service" -> "Serviced here"; else -> "Visited" })
                            Row(Modifier.padding(start = 2.dp, top = 4.dp), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                r.priceHonesty?.let { Chip("Bill vs quote $it/5", if (it >= 4) Good else Amber) }
                                r.noForcedAddons?.let { Chip(if (it == 1) "No forced add-ons" else "Pushed add-ons", if (it == 1) Good else Amber) }
                                r.deliveryOnTime?.let { Chip(if (it == 1) "Delivered on time" else "Delivery late", if (it == 1) Good else Amber) }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ReviewItem(author: String, stars: Int?, whenText: String?, text: String, tag: String) {
    var open by remember { mutableStateOf(false) }
    Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(14.dp)).border(1.dp, Line, RoundedCornerShape(14.dp)).clickable { open = !open }.padding(12.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(32.dp).clip(CircleShape).background(Electric.copy(alpha = 0.18f)), contentAlignment = Alignment.Center) {
                Text(author.take(1).uppercase(), color = Electric, fontWeight = FontWeight.Bold)
            }
            Spacer(Modifier.width(10.dp))
            Column(Modifier.weight(1f)) {
                Text(author, fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Text(listOfNotNull(stars?.let { "★".repeat(it.coerceIn(0, 5)) + "☆".repeat(5 - it.coerceIn(0, 5)) }, whenText, tag).joinToString(" · "),
                    color = Amber, style = MaterialTheme.typography.bodySmall)
            }
        }
        if (text.isNotBlank()) Text(text, style = MaterialTheme.typography.bodyMedium, maxLines = if (open) Int.MAX_VALUE else 4,
            overflow = TextOverflow.Ellipsis, modifier = Modifier.padding(top = 8.dp))
    }
}
