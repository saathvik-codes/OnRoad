package com.onroad.app.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
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

private enum class Tab(val label: String) { Price("On-road price"), Emi("EMI & loans"), Specs("Specs & features"), Safety("Safety"), Showrooms("Showrooms"), Offers("Offers") }

@Composable
fun ModelScreen(id: String, onBack: () -> Unit, onSignIn: () -> Unit = {}, vm: BrowseVM = hiltViewModel()) {
    val city by vm.prefs.city.collectAsStateWithLifecycle()
    var m by remember { mutableStateOf<ModelDetail?>(null) }
    var err by remember { mutableStateOf<String?>(null) }
    var sel by remember { mutableStateOf<String?>(null) }
    var tab by remember { mutableStateOf(Tab.Price) }
    var specs by remember { mutableStateOf<VariantSpecs?>(null) }
    var rates by remember { mutableStateOf<List<com.onroad.app.data.LoanRate>>(emptyList()) }
    val acc by vm.prefs.account.collectAsStateWithLifecycle()
    val scope = androidx.compose.runtime.rememberCoroutineScope()
    var askQuote by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) { rates = runCatching { vm.api.loanRates() }.getOrElse { emptyList() } }
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
    // the costliest variant's equipment = everything the model offers; used to show what this variant lacks
    var topSpecs by remember { mutableStateOf<VariantSpecs?>(null) }
    val topId = model.variants.filter { it.exShowroomInr != null }.maxByOrNull { it.exShowroomInr!! }?.id
    LaunchedEffect(topId) { topSpecs = topId?.let { runCatching { vm.api.specs(it) }.getOrNull() } }
    val prices = model.variants.mapNotNull { it.exShowroomInr }

    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 32.dp)) {
        item {
            Row(Modifier.statusBarsPadding().padding(4.dp), verticalAlignment = Alignment.CenterVertically) {
                IconButton(onBack) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "Back") }
                Text(model.brandName, color = Mute)
            }
            AsyncImage(vm.prefs.img(model.imageUrl, 1200), model.name, contentScale = ContentScale.Fit,
                modifier = Modifier.fillMaxWidth().aspectRatio(16 / 9f).padding(horizontal = 12.dp))
            Column(Modifier.padding(horizontal = 20.dp)) {
                Text(model.name, style = MaterialTheme.typography.displaySmall)
                Text(range(prices.minOrNull(), prices.maxOrNull()), style = MaterialTheme.typography.titleLarge, color = Ignition)
                Text("Ex-showroom · ${variant?.priceCity ?: city} · ${model.variants.size} variants", color = Mute)
                Spacer(Modifier.height(12.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    androidx.compose.material3.Button(onClick = { if (acc == null) onSignIn() else askQuote = true }, Modifier.weight(1f).height(48.dp),
                        colors = androidx.compose.material3.ButtonDefaults.buttonColors(containerColor = Ignition)) { Text("Get dealer quotes", fontWeight = FontWeight.SemiBold) }
                    androidx.compose.material3.OutlinedButton(onClick = {
                        val v = variant ?: return@OutlinedButton
                        if (acc == null) onSignIn() else scope.launch {
                            runCatching { vm.api.save(com.onroad.app.data.SaveIn(v.id, city)) }
                                .onSuccess { android.widget.Toast.makeText(ctx, "Saved to your garage. We'll track its price.", android.widget.Toast.LENGTH_SHORT).show() }
                        }
                    }, Modifier.height(48.dp)) { Icon(Icons.Outlined.BookmarkAdd, "Save", tint = Ink) }
                }
            }
            Spacer(Modifier.height(14.dp))
            LazyRow(contentPadding = PaddingValues(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                items(model.variants, key = { it.id }) { v ->
                    val on = v.id == variant?.id
                    Column(Modifier.clip(RoundedCornerShape(16.dp)).background(if (on) Ignition.copy(alpha = 0.16f) else Panel)
                        .border(1.dp, if (on) Ignition else Line, RoundedCornerShape(16.dp)).clickable { sel = v.id }.padding(12.dp).width(170.dp)) {
                        Text(v.name, style = MaterialTheme.typography.labelLarge, maxLines = 1)
                        Text(listOfNotNull(v.fuel, v.transmission).joinToString(" · "), color = Mute, style = MaterialTheme.typography.bodyMedium, maxLines = 1)
                        Text(lakh(v.exShowroomInr), fontWeight = FontWeight.Bold)
                    }
                }
            }
            Row(Modifier.horizontalScroll(rememberScrollState()).padding(16.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Tab.entries.filter { it != Tab.Offers || model.offers.isNotEmpty() }.forEach { t ->
                    Text(t.label, style = MaterialTheme.typography.labelLarge, color = if (t == tab) androidx.compose.ui.graphics.Color.White else Mute,
                        modifier = Modifier.clip(RoundedCornerShape(50)).background(if (t == tab) Ignition else Panel2).clickable { tab = t }
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
            }
            Tab.Emi -> item {
                val total = variant?.onroad?.let { it.totalInr - it.refundableInr }
                Column(Modifier.padding(horizontal = 16.dp)) {
                    if (total == null || total <= 0) Text("This variant has no published price.", color = Mute)
                    else EmiCard(total, variant.fuel == "Electric", rates) { u -> ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(u))) }
                }
            }
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
    }
    if (askQuote) variant?.let { v -> QuoteSheet(v.id, v.name, city, onClose = { askQuote = false }, vm = vm) }
}
