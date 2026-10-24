package com.onroad.app.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
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
    Icon(Icons.Outlined.CloudOff, null, tint = Mute, modifier = Modifier.size(40.dp))
    Text(message, color = Mute, textAlign = TextAlign.Center)
    Button(onRetry, colors = ButtonDefaults.buttonColors(containerColor = Panel2)) { Text("Try again", color = Ink) }
}

/** Nearest official showrooms of every brand (or one brand) by distance from the phone, with call and directions. */
@Composable
fun ShowroomsScreen(onBack: () -> Unit, vm: BrowseVM = hiltViewModel()) {
    val ctx = LocalContext.current
    var type by remember { mutableStateOf("car") }
    var brand by remember { mutableStateOf<String?>(null) }
    var brands by remember { mutableStateOf<List<Brand>>(emptyList()) }
    var list by remember { mutableStateOf<List<NearDealer>?>(null) }
    var err by remember { mutableStateOf<String?>(null) }
    val cityNow by vm.prefs.city.collectAsStateWithLifecycle()
    var here by remember { mutableStateOf(vm.prefs.lat?.let { la -> vm.prefs.lng?.let { lo -> la to lo } }) }
    // picking another city moves the search there (its centre), so showrooms always match the chosen city
    LaunchedEffect(cityNow) { vm.prefs.lat?.let { la -> vm.prefs.lng?.let { lo -> if (here != la to lo) here = la to lo } } }
    var tick by remember { mutableIntStateOf(0) }
    var rating by remember { mutableStateOf<NearDealer?>(null) }
    val city = vm.prefs.city.value
    var locOff by remember { mutableStateOf(false) }
    val locate = rememberLocator(vm.prefs) { loc, problem ->
        locOff = problem == com.onroad.app.data.LocationProblem.Off
        if (loc != null && (loc.latitude !in 6.0..37.5 || loc.longitude !in 68.0..97.5))
            err = "Your phone reports a location outside India, so there are no showrooms to show. Turn on precise location and try again."
        else if (loc != null) here = loc.latitude to loc.longitude
        else err = (problem ?: com.onroad.app.data.LocationProblem.NoFix).message
    }
    LaunchedEffect(Unit) { if (here == null) locate() }
    LaunchedEffect(type) { brands = runCatching { vm.api.brands(city, type) }.getOrElse { emptyList() }.filter { it.models > 0 }.sortedByDescending { it.models } }
    LaunchedEffect(here, type, brand, tick) {
        val h = here ?: return@LaunchedEffect
        list = null; err = null
        runCatching { vm.api.dealersNear(h.first, h.second, brand, type) }
            .onSuccess { list = it }.onFailure { err = "Couldn't reach OnRoad. Check your connection." }
    }
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 24.dp)) {
        item {
            ScreenHeader("Showrooms near you", "Official dealers, nearest first", onBack)
            Column(Modifier.padding(horizontal = 16.dp)) {
                Pills(listOf("car" to "Car showrooms", "bike" to "Bike showrooms"), type) { type = it; brand = null }
            }
            LazyRow(contentPadding = PaddingValues(16.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                item { BrandPill("All brands", brand == null) { brand = null } }
                items(brands, key = { it.slug }) { b -> BrandPill(b.name, brand == b.slug) { brand = b.slug } }
            }
        }
        val l = list
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
            l.isEmpty() -> item { Text("No listed showroom within about 300 km. Try another brand.", color = Mute, modifier = Modifier.padding(20.dp)) }
            else -> items(l, key = { it.id }) { d ->
                Tile(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 6.dp), pad = 14) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Chip(d.brandName, Ignition); Spacer(Modifier.width(8.dp))
                                d.distanceKm?.let { Text("%.1f km".format(it), color = Electric, fontWeight = FontWeight.SemiBold) }
                            }
                            Spacer(Modifier.height(6.dp))
                            Text(d.name, style = MaterialTheme.typography.titleMedium, maxLines = 2, overflow = TextOverflow.Ellipsis)
                            Text(listOfNotNull(d.address.ifBlank { null }, d.city).joinToString(", "), color = Mute,
                                style = MaterialTheme.typography.bodySmall, maxLines = 2)
                            Row(Modifier.padding(top = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                                if (d.ratingCount > 0) {
                                    Text("★ ${d.rating}", color = Amber, fontWeight = FontWeight.SemiBold)
                                    Text("  ${d.ratingCount} OnRoad buyer${if (d.ratingCount > 1) "s" else ""}", color = Mute, style = MaterialTheme.typography.bodySmall)
                                    Spacer(Modifier.width(12.dp))
                                }
                                Text("Rate this showroom", color = Ignition, style = MaterialTheme.typography.labelLarge,
                                    modifier = Modifier.clickable { rating = d })
                            }
                        }
                        Column {
                            d.phone?.let { ph ->
                                IconButton({ ctx.startActivity(Intent(Intent.ACTION_DIAL, Uri.parse("tel:" + ph.split(',', '/', ';')[0].trim()))) }) {
                                    Icon(Icons.Outlined.Call, "Call", tint = Good)
                                }
                            }
                            if (d.lat != null && d.lng != null) IconButton({
                                ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://www.google.com/maps/dir/?api=1&destination=${d.lat},${d.lng}")))
                            }) { Icon(Icons.Outlined.Directions, "Directions", tint = Electric) }
                        }
                    }
                }
            }
        }
        item {
            Row(Modifier.fillMaxWidth().padding(16.dp).clickable { here = null; locate() }, horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Outlined.MyLocation, null, tint = Mute, modifier = Modifier.size(16.dp)); Spacer(Modifier.width(6.dp))
                Text("Refresh my location", color = Mute)
            }
        }
    }
    rating?.let { d -> RateSheet(d, vm) { posted -> rating = null; if (posted) tick++ } }
}

/** A buyer rates the showroom they dealt with: overall stars, price honesty, add-on pressure, delivery. Needs sign-in. */
@OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)
@Composable
private fun RateSheet(d: NearDealer, vm: BrowseVM, onDone: (Boolean) -> Unit) {
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
            modifier = Modifier.clip(RoundedCornerShape(50)).background(if (v == b) Ignition else Panel2).clickable { set(b) }.padding(horizontal = 14.dp, vertical = 7.dp)) }
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
            }, Modifier.fillMaxWidth().height(50.dp), enabled = !busy, colors = ButtonDefaults.buttonColors(containerColor = Ignition)) {
                Text(if (busy) "Posting…" else "Post rating", fontWeight = FontWeight.SemiBold)
            }
        }
    }
}

@Composable
private fun BrandPill(label: String, on: Boolean, onClick: () -> Unit) = Text(label, style = MaterialTheme.typography.labelLarge,
    color = if (on) Color.White else Mute,
    modifier = Modifier.clip(RoundedCornerShape(50)).background(if (on) Ignition else Panel2).clickable(onClick = onClick)
        .padding(horizontal = 14.dp, vertical = 9.dp))
