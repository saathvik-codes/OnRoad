package com.onroad.app.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.Call
import androidx.compose.material.icons.outlined.BookmarkAdd
import androidx.compose.material.icons.outlined.Directions
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.Shield
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import kotlinx.coroutines.launch
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil3.compose.AsyncImage
import com.onroad.app.data.ModelDetail
import com.onroad.app.data.VariantSpecs

private enum class Tab(val label: String) { Price("On-road price"), Specs("Specs & features"), Ownership("Insurance & RTA"), Emi("EMI & loans"),
    Safety("Safety"), Showrooms("Showrooms"), Offers("Offers") }

@Composable
fun ModelScreen(id: String, onBack: () -> Unit, onSignIn: () -> Unit = {}, onModel: (String) -> Unit = {}, vm: BrowseVM = hiltViewModel()) {
    val city by vm.prefs.city.collectAsStateWithLifecycle()
    var rateDealer by remember { mutableStateOf<com.onroad.app.data.Dealer?>(null) }
    var m by remember { mutableStateOf<ModelDetail?>(null) }
    var err by remember { mutableStateOf<String?>(null) }
    var sel by remember { mutableStateOf<String?>(null) }
    var tab by remember { mutableStateOf(Tab.Price) }
    var specs by remember { mutableStateOf<VariantSpecs?>(null) }
    var rates by remember { mutableStateOf<List<com.onroad.app.data.LoanRate>>(emptyList()) }
    val acc by vm.prefs.account.collectAsStateWithLifecycle()
    val scope = androidx.compose.runtime.rememberCoroutineScope()
    var askQuote by remember { mutableStateOf(false) }
    var picking by remember { mutableStateOf(false) }
    var ownership by remember { mutableStateOf<com.onroad.app.data.Ownership?>(null) }
    var ownFailed by remember { mutableStateOf(false) }
    LaunchedEffect(m?.id) { m?.let { md -> rates = runCatching { vm.api.loanRates(md.brandVehicleType ?: md.vehicleType ?: "car") }.getOrElse { emptyList() } } }
    val ctx = LocalContext.current
    LaunchedEffect(id, city) {
        val (b, s) = id.split("/", limit = 2)
        runCatching { vm.api.model(b, s, city, vm.prefs.lat, vm.prefs.lng) }.onSuccess { m = it } .onFailure { e -> android.util.Log.e("model", "load failed", e); err = "Couldn't load this car." }
    }
    var retry by remember { mutableStateOf(0) }
    LaunchedEffect(retry) { if (retry > 0) { err = null; val (b2, s2) = id.split("/", limit = 2)
        runCatching { vm.api.model(b2, s2, city, vm.prefs.lat, vm.prefs.lng) }.onSuccess { m = it }.onFailure { err = "Couldn't load this car. Check your connection." } } }
    val model = m ?: return Column(Modifier.fillMaxSize()) {
        ScreenHeader("", null, onBack)
        Column(Modifier.fillMaxWidth().padding(top = 100.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            if (err == null) CircularProgressIndicator(color = Ignition)
            else { Text(err!!, color = Mute); androidx.compose.material3.TextButton({ retry++ }) { Text("Try again", color = Ignition) } }
        }
    }
    val variant = model.variants.firstOrNull { it.id == sel } ?: model.variants.firstOrNull { it.exShowroomInr != null } ?: model.variants.firstOrNull()
    LaunchedEffect(variant?.id) { specs = null; specs = variant?.let { v -> runCatching { vm.api.specs(v.id) }.getOrNull() } }
    LaunchedEffect(variant?.id, city, tab) {
        if (tab == Tab.Ownership && variant != null) { ownership = null; ownFailed = false
            runCatching { vm.api.ownership(variant.id, city) }.onSuccess { ownership = it }.onFailure { ownFailed = true } }
    }
    LaunchedEffect(model.id) { com.onroad.app.data.Track.viewCar(model.id, model.brandSlug, city, model.variants.mapNotNull { it.exShowroomInr }.minOrNull()) }
    LaunchedEffect(sel) { sel?.let { s -> com.onroad.app.data.Track.pickVariant(s, variant?.onroad?.let { it.totalInr - it.refundableInr }) } }
    // the costliest variant's equipment = everything the model offers; used to show what this variant lacks
    var topSpecs by remember { mutableStateOf<VariantSpecs?>(null) }
    val topId = model.variants.filter { it.exShowroomInr != null }.maxByOrNull { it.exShowroomInr!! }?.id
    LaunchedEffect(topId) { topSpecs = topId?.let { runCatching { vm.api.specs(it) }.getOrNull() } }
    val prices = model.variants.mapNotNull { it.exShowroomInr }

    Box(Modifier.fillMaxSize()) {
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 110.dp)) {
        item {
            Row(Modifier.fillMaxWidth().statusBarsPadding().padding(4.dp), verticalAlignment = Alignment.CenterVertically) {
                IconButton(onBack) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "Back") }
                Text(model.brandName, color = Mute, modifier = Modifier.weight(1f))
                IconButton({
                    val v = variant ?: return@IconButton
                    if (acc == null) onSignIn() else scope.launch {
                        com.onroad.app.data.Track.saveCar(v.id)
                        runCatching { vm.api.save(com.onroad.app.data.SaveIn(v.id, city)) }
                            .onSuccess { android.widget.Toast.makeText(ctx, "Saved to your garage. We'll alert you when the price drops.", android.widget.Toast.LENGTH_SHORT).show() }
                    }
                }) { Icon(Icons.Outlined.BookmarkAdd, "Save and track price", tint = Ink) }
            }
            Gallery(model.gallery.ifEmpty { listOfNotNull(model.imageUrl?.let { com.onroad.app.data.GalleryItem(it, model.name) }) },
                variant?.imageUrl, variant?.name) { u -> vm.prefs.img(u, 1200) }
            Column(Modifier.padding(horizontal = 20.dp)) {
                Text(model.name, style = MaterialTheme.typography.displaySmall)
                Text(range(prices.minOrNull(), prices.maxOrNull()), style = MaterialTheme.typography.titleLarge, color = Ignition)
                val pc = variant?.priceCity
                Text(when {
                    pc == null || pc.equals(city, true) -> "Ex-showroom price in $city"
                    pc == "India (national)" -> "Ex-showroom · same price across India"
                    else -> "Ex-showroom · $city (${model.brandName} lists the nearest price, $pc)"
                } + " · ${model.variants.size} variants", color = Mute)
            }
            // key specs at a glance (engine, power, mileage / range, seats), from this variant's official sheet
            Spacer(Modifier.height(14.dp))
            VariantCard(variant, model.variants.size) { picking = true }
            val glance = HEADLINE_SPECS.mapNotNull { (label, rx) -> findSpec(specs?.specs, rx)?.let { label to it } }.take(6)
            if (glance.isNotEmpty()) Column(Modifier.padding(start = 16.dp, end = 16.dp, top = 12.dp)) { KeySpecGrid(glance) }
            Row(Modifier.horizontalScroll(rememberScrollState()).padding(16.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Tab.entries.filter { it != Tab.Offers || model.offers.isNotEmpty() }.forEach { t ->
                    Text(t.label, style = MaterialTheme.typography.labelLarge, color = if (t == tab) androidx.compose.ui.graphics.Color.White else Mute,
                        modifier = Modifier.clip(Corner).background(if (t == tab) Ignition else Panel2).clickable { tab = t }
                            .padding(horizontal = 14.dp, vertical = 8.dp))
                }
            }
        }
        when (tab) {
            Tab.Price -> item {
                val b = variant?.onroad
                Tile(Modifier.fillMaxWidth().padding(horizontal = 16.dp)) {
                    if (b == null) Text("This variant has no published price.", color = Mute) else Column {
                        Text("ON-ROAD IN ${b.stateName.uppercase()}", style = MaterialTheme.typography.labelSmall, color = Mute)
                        Text(rupees(b.totalInr - b.refundableInr), style = MaterialTheme.typography.displaySmall)
                        if (b.refundableInr > 0) Text("+ ${rupees(b.refundableInr)} TCS, which you get back in your tax return", color = Mute)
                        Spacer(Modifier.height(10.dp))
                        b.lines.filter { !it.refundable }.forEach { l ->
                            Row(Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
                                Column(Modifier.weight(1f)) { Text(l.label, style = MaterialTheme.typography.titleMedium); Text(l.basis, color = Mute, style = MaterialTheme.typography.bodyMedium) }
                                Text(if (l.amountInr != null) rupees(l.amountInr) else "—", fontWeight = FontWeight.SemiBold)
                            }
                        }
                    }
                }
                variant?.let { v -> PriceTrend(model.priceHistory, v.id, v.priceCity ?: city) }
            }
            Tab.Emi -> item {
                val total = variant?.onroad?.let { it.totalInr - it.refundableInr }
                Column(Modifier.padding(horizontal = 16.dp)) {
                    if (total == null || total <= 0) Text("This variant has no published price.", color = Mute)
                    else EmiCard(total, variant.fuel == "Electric", rates) { u -> ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(u))) }
                }
            }
            Tab.Ownership -> item { OwnershipTab(ownership, model.brandName, ownFailed) }
            Tab.Specs -> item {
                SpecsSection(model.brandName, variant?.name ?: "", specs, topSpecs) { u -> vm.prefs.img(u, 640) }
            }
            Tab.Safety -> if (model.crashTests.isEmpty()) item {
                Text("No official Bharat NCAP or Global NCAP result on record for the ${model.name}.", color = Mute, modifier = Modifier.padding(20.dp))
            } else items(model.crashTests, key = { it.sourceUrl + it.protocol }) { t ->
                Tile(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 6.dp).clickable { ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(t.videoUrl ?: t.sourceUrl))) }) {
                    Column {
                        Row(verticalAlignment = Alignment.CenterVertically) { Icon(Icons.Outlined.Shield, null, tint = Good); Spacer(Modifier.width(6.dp)); Text(t.agency, color = Good, fontWeight = FontWeight.Bold) }
                        Text(listOfNotNull(t.protocol, t.ratingPublished).joinToString(" · "), color = Mute)
                        Spacer(Modifier.height(8.dp))
                        Text("Adult ${t.adultStars ?: "—"}★   Child ${t.childStars ?: "—"}★", style = MaterialTheme.typography.titleLarge)
                        Text(if (t.videoUrl != null) "Tap to watch the official crash test" else "Tap for the official result", color = Electric)
                    }
                }
            }
            Tab.Showrooms -> if (model.dealers.isEmpty()) item { Text("No showroom listed for $city.", color = Mute, modifier = Modifier.padding(20.dp)) }
            else items(model.dealers, key = { it.id }) { d ->
                Tile(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 6.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text(d.name, style = MaterialTheme.typography.titleMedium); Text(d.address, color = Mute, maxLines = 2)
                            d.distanceKm?.let { Text("%.1f km away".format(it), color = Electric, style = MaterialTheme.typography.labelLarge) }
                            Row(Modifier.padding(top = 4.dp), verticalAlignment = Alignment.CenterVertically) {
                                d.googleRating?.let { g -> Text("★ %.1f".format(g), color = Amber, fontWeight = FontWeight.Bold)
                                    Text(" Google${d.googleCount?.let { " (%,d)".format(it) } ?: ""}   ", color = Mute, style = MaterialTheme.typography.bodySmall) }
                                d.onroadRating?.takeIf { d.onroadCount > 0 }?.let { r -> Text("★ %.1f".format(r), color = Good, fontWeight = FontWeight.Bold)
                                    Text(" ${d.onroadCount} OnRoad buyer${if (d.onroadCount > 1) "s" else ""}   ", color = Mute, style = MaterialTheme.typography.bodySmall) }
                                Text("Rate", color = Ignition, style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.SemiBold,
                                    modifier = Modifier.clickable { rateDealer = d })
                            }
                        }
                        if (d.lat != null && d.lng != null) IconButton({ ctx.startActivity(Intent(Intent.ACTION_VIEW,
                            Uri.parse("https://www.google.com/maps/dir/?api=1&destination=${d.lat},${d.lng}"))) }) { Icon(Icons.Outlined.Directions, "Directions", tint = Electric) }
                        d.phone?.let { ph -> IconButton({ ctx.startActivity(Intent(Intent.ACTION_DIAL, Uri.parse("tel:" + ph.split(',', '/')[0].trim()))) }) {
                            Icon(Icons.Outlined.Call, "Call", tint = Ignition) } }
                    }
                }
            }
            Tab.Offers -> items(model.offers, key = { it.title + it.amountInr }) { o ->
                Tile(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 6.dp)) {
                    Column {
                        Text(o.title, style = MaterialTheme.typography.titleMedium)
                        o.amountInr?.let { Text(rupees(it), color = Good, style = MaterialTheme.typography.titleLarge) }
                        o.validUntil?.let { Text("Valid until $it", color = Mute) }
                        (o.conditions ?: o.details).takeIf { it.isNotBlank() }?.let { Text(it, color = Mute, style = MaterialTheme.typography.bodyMedium) }
                    }
                }
            }
        }
        item { SimilarRow(model, city, vm, onOpen = onModel) }
        item { AdBanner() }
    }
    // pinned: this variant's on-road price and the main action, always in reach
    val onRoad = variant?.onroad?.let { it.totalInr - it.refundableInr }
    Row(Modifier.align(Alignment.BottomCenter).fillMaxWidth().background(Panel).border(1.dp, Line)
        .navigationBarsPadding().padding(horizontal = 16.dp, vertical = 10.dp), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) {
            Text(if (onRoad != null) "On-road · ${variant?.name ?: ""}" else "Price", style = MaterialTheme.typography.labelMedium, color = Mute,
                maxLines = 1, overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis)
            Text(onRoad?.let { lakh(it) } ?: lakh(variant?.exShowroomInr), style = MaterialTheme.typography.titleLarge)
        }
        androidx.compose.material3.Button(onClick = { if (acc == null) onSignIn() else askQuote = true }, Modifier.height(50.dp),
            colors = androidx.compose.material3.ButtonDefaults.buttonColors(containerColor = Ignition), shape = Corner) {
            Text("Get best price", fontWeight = FontWeight.SemiBold)
        }
    }
    }
    rateDealer?.let { d ->
        RateSheet(com.onroad.app.data.NearDealer(d.id, model.brandSlug, model.brandName, d.name, d.address, d.city, d.phone, d.lat, d.lng), vm) { posted ->
            rateDealer = null; if (posted) retry++
        }
    }
    if (askQuote) variant?.let { v -> QuoteSheet(v.id, v.name, city, onClose = { askQuote = false }, vm = vm) }
    if (picking) VariantPicker(model.variants, variant?.id, onPick = { sel = it }, onClose = { picking = false })
}
