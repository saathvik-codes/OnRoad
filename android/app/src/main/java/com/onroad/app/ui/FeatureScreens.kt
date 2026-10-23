package com.onroad.app.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.automirrored.outlined.OpenInNew
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.LocalOffer
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil3.compose.AsyncImage
import com.onroad.app.data.LoanRate
import com.onroad.app.data.OfferItem
import com.onroad.app.data.Reco
import kotlinx.coroutines.launch
import kotlin.math.pow
import kotlin.math.roundToLong

@Composable
fun ScreenHeader(title: String, sub: String? = null, onBack: () -> Unit) = Row(
    Modifier.fillMaxWidth().statusBarsPadding().padding(start = 4.dp, end = 16.dp, top = 6.dp, bottom = 4.dp), verticalAlignment = Alignment.CenterVertically,
) {
    IconButton(onBack) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "Back") }
    Column { Text(title, style = MaterialTheme.typography.titleLarge); sub?.let { Text(it, color = Mute, style = MaterialTheme.typography.bodyMedium) } }
}

@Composable
fun Pills(options: List<Pair<String, String>>, sel: String, onSel: (String) -> Unit) =
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        options.forEach { (k, l) ->
            Text(l, style = MaterialTheme.typography.labelLarge, color = if (sel == k) Color.White else Mute,
                modifier = Modifier.clip(RoundedCornerShape(50)).background(if (sel == k) Ignition else Panel2)
                    .clickable { onSel(k) }.padding(horizontal = 14.dp, vertical = 9.dp))
        }
    }

// ---------------------------------------------------------------- offers
@Composable
fun OfferCard(o: OfferItem, img: String?, modifier: Modifier = Modifier, onOpen: () -> Unit) = Tile(modifier.clickable(onClick = onOpen), pad = 14) {
    Column {
        Row(verticalAlignment = Alignment.CenterVertically) {
            if (img != null) AsyncImage(img, o.modelName, contentScale = ContentScale.Fit, modifier = Modifier.width(96.dp).aspectRatio(16 / 10f))
            else Box(Modifier.size(56.dp).clip(RoundedCornerShape(14.dp)).background(Ignition.copy(alpha = 0.14f)), contentAlignment = Alignment.Center) {
                Icon(Icons.Outlined.LocalOffer, null, tint = Ignition)
            }
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(listOfNotNull(o.brandName, o.modelName).joinToString(" "), style = MaterialTheme.typography.titleMedium, maxLines = 1, overflow = TextOverflow.Ellipsis)
                o.amountInr?.let { Text("Benefits up to ${rupees(it)}", color = Good, fontWeight = FontWeight.SemiBold) }
                o.validUntil?.let { Text("Valid till $it", color = Amber, style = MaterialTheme.typography.bodySmall) }
            }
        }
        Spacer(Modifier.height(8.dp))
        Text(o.title, style = MaterialTheme.typography.bodyMedium, maxLines = 3, overflow = TextOverflow.Ellipsis)
        Text("From ${o.brandName ?: "the manufacturer"}'s official site. Final benefits are confirmed by the dealer.", color = Mute,
            style = MaterialTheme.typography.bodySmall, modifier = Modifier.padding(top = 6.dp))
    }
}

@Composable
fun OffersScreen(onBack: () -> Unit, vm: BrowseVM = hiltViewModel()) {
    val city by vm.prefs.city.collectAsStateWithLifecycle()
    var list by remember { mutableStateOf<List<OfferItem>?>(null) }
    var brand by remember { mutableStateOf("all") }
    val ctx = LocalContext.current
    var failed by remember { mutableStateOf(false) }
    var tick by remember { mutableIntStateOf(0) }
    LaunchedEffect(city, tick) {
        failed = false; list = null
        runCatching { vm.api.offers(city, 120) }.onSuccess { list = it }.onFailure { failed = true }
    }
    Column(Modifier.fillMaxSize()) {
        ScreenHeader("Offers & festive deals", "Live from manufacturers · $city", onBack)
        val l = list
        if (failed) ErrorState("Couldn't reach OnRoad. Check your connection.") { tick++ }
        else if (l == null) Box(Modifier.fillMaxWidth().padding(40.dp), contentAlignment = Alignment.Center) { CircularProgressIndicator(color = Ignition) }
        else if (l.isEmpty()) Text("No manufacturer offers listed for $city right now.", color = Mute, modifier = Modifier.padding(20.dp))
        else {
            val brands = listOf("all" to "All") + l.mapNotNull { o -> o.brandName?.let { o.brandSlug to it } }.distinct()
            Box(Modifier.padding(horizontal = 16.dp, vertical = 6.dp)) { Pills(brands.take(12), brand) { brand = it } }
            LazyColumn(contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                items(l.filter { brand == "all" || it.brandSlug == brand }, key = { it.id }) { o ->
                    OfferCard(o, vm.prefs.img(o.modelImage, 400), Modifier.fillMaxWidth()) {
                        o.sourceUrl?.let { ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(it))) }
                    }
                }
            }
        }
    }
}

// ---------------------------------------------------------------- finder
@Composable
fun FinderScreen(onBack: () -> Unit, onModel: (String) -> Unit, vm: BrowseVM = hiltViewModel()) {
    val city by vm.prefs.city.collectAsStateWithLifecycle()
    var type by remember { mutableStateOf("car") }
    var budget by remember { mutableFloatStateOf(12f) }           // lakh, on-road
    var usage by remember { mutableStateOf("mixed") }
    var seats by remember { mutableIntStateOf(5) }
    var fuel by remember { mutableStateOf("any") }
    var trans by remember { mutableStateOf("any") }
    var km by remember { mutableFloatStateOf(1000f) }
    var prio by remember { mutableStateOf("value") }
    var res by remember { mutableStateOf<List<Reco>?>(null) }
    var busy by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val bike = type == "bike"
    val maxB = if (bike) 6f else 60f

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).navigationBarsPadding()) {
        ScreenHeader("Find my ${if (bike) "bike" else "car"}", "Picks from official prices, crash tests and specs", onBack)
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Pills(listOf("car" to "Car", "bike" to "Bike / scooter"), type) { type = it; budget = if (it == "bike") 1.5f else 12f; res = null }
            Tile(Modifier.fillMaxWidth()) {
                Column {
                    Text("On-road budget", color = Mute, style = MaterialTheme.typography.labelSmall)
                    Text("₹%.1f lakh".format(budget), style = MaterialTheme.typography.headlineSmall)
                    Slider(budget, { budget = it }, valueRange = (if (bike) 0.5f else 4f)..maxB,
                        colors = SliderDefaults.colors(thumbColor = Ignition, activeTrackColor = Ignition))
                }
            }
            Text("How will you use it?", fontWeight = FontWeight.SemiBold)
            Pills(listOf("city" to "Mostly city", "mixed" to "City + highway", "highway" to "Long drives"), usage) { usage = it }
            if (!bike) { Text("Seats you need", fontWeight = FontWeight.SemiBold); Pills(listOf("4" to "4", "5" to "5", "7" to "6–7"), seats.toString()) { seats = it.toInt() } }
            Text("Fuel", fontWeight = FontWeight.SemiBold)
            Pills(listOf("any" to "Any", "Petrol" to "Petrol") + (if (bike) emptyList() else listOf("Diesel" to "Diesel", "CNG" to "CNG")) + listOf("Electric" to "Electric"), fuel) { fuel = it }
            if (!bike) { Text("Gearbox", fontWeight = FontWeight.SemiBold); Pills(listOf("any" to "Any", "Manual" to "Manual", "Automatic" to "Automatic"), trans) { trans = it } }
            Text("Monthly running: ${km.toInt()} km", fontWeight = FontWeight.SemiBold)
            Slider(km, { km = it }, valueRange = 200f..4000f, steps = 18, colors = SliderDefaults.colors(thumbColor = Ignition, activeTrackColor = Ignition))
            Text("What matters most?", fontWeight = FontWeight.SemiBold)
            Pills(listOf("value" to "Value", "safety" to "Safety", "mileage" to "Mileage", "features" to "Features", "performance" to "Performance"), prio) { prio = it }
            Button(onClick = {
                busy = true
                scope.launch {
                    res = runCatching {
                        vm.api.recommendations(city, type, (budget * 100_000).roundToLong(), usage, if (bike) 0 else seats,
                            fuel.takeIf { it != "any" }, trans.takeIf { it != "any" }, km.toInt(),
                            listOf(prio, "value", "safety").distinct().joinToString(","))
                    }.getOrElse { emptyList() }
                    busy = false
                }
            }, Modifier.fillMaxWidth().height(54.dp), enabled = !busy, colors = ButtonDefaults.buttonColors(containerColor = Ignition)) {
                Icon(Icons.Outlined.AutoAwesome, null); Spacer(Modifier.width(8.dp)); Text(if (busy) "Finding…" else "Show my matches", fontWeight = FontWeight.SemiBold)
            }
            res?.let { r ->
                if (r.isEmpty()) Text("Nothing fits all of that. Try a higher budget or fewer filters.", color = Mute)
                r.forEachIndexed { i, x ->
                    Tile(Modifier.fillMaxWidth().clickable { onModel(x.id) }, pad = 14) {
                        Column {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                AsyncImage(vm.prefs.img(x.imageUrl, 400), x.name, contentScale = ContentScale.Fit, modifier = Modifier.width(110.dp).aspectRatio(16 / 10f))
                                Spacer(Modifier.width(12.dp))
                                Column(Modifier.weight(1f)) {
                                    Chip(if (i == 0) "Best match · ${x.matchScore}%" else "${x.matchScore}% match", if (i == 0) Ignition else Electric)
                                    Text("${x.brand} ${x.name}", style = MaterialTheme.typography.titleMedium, maxLines = 1, overflow = TextOverflow.Ellipsis)
                                    x.variant?.let { Text(it, color = Mute, style = MaterialTheme.typography.bodySmall, maxLines = 1, overflow = TextOverflow.Ellipsis) }
                                }
                            }
                            Spacer(Modifier.height(8.dp))
                            x.reasons.forEach { reason ->
                                Row(Modifier.padding(vertical = 2.dp)) {
                                    Icon(Icons.Outlined.CheckCircle, null, tint = Good, modifier = Modifier.size(16.dp).padding(top = 2.dp)); Spacer(Modifier.width(6.dp))
                                    Text(reason, style = MaterialTheme.typography.bodyMedium)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

// ---------------------------------------------------------------- EMI
/** EMI on the on-road price with live bank rates (each bank's own published starting rate). */
@Composable
fun EmiCard(onRoad: Long, electric: Boolean, rates: List<LoanRate>, open: (String) -> Unit) {
    var downPct by remember { mutableFloatStateOf(20f) }
    var years by remember { mutableIntStateOf(5) }
    val usable = rates.filter { it.minPct != null && (electric || it.evOnly == 0) }.sortedBy { it.minPct }
    var bank by remember(usable) { mutableStateOf(usable.firstOrNull()) }
    val rate = bank?.minPct ?: 9.0
    val loan = (onRoad * (1 - downPct / 100)).roundToLong()
    val r = rate / 1200; val n = years * 12
    val emi = if (r == 0.0) loan / n else (loan * r * (1 + r).pow(n) / ((1 + r).pow(n) - 1)).roundToLong()
    Tile(Modifier.fillMaxWidth()) {
        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("EMI", color = Mute, style = MaterialTheme.typography.labelSmall)
            Row(verticalAlignment = Alignment.Bottom) {
                Text(rupees(emi), style = MaterialTheme.typography.headlineMedium); Text(" /month", color = Mute)
            }
            Text("Loan ${rupees(loan)} at $rate% for $years years · down payment ${rupees(onRoad - loan)}", color = Mute, style = MaterialTheme.typography.bodyMedium)
            Text("Down payment ${downPct.toInt()}%", style = MaterialTheme.typography.labelLarge)
            Slider(downPct, { downPct = it }, valueRange = 10f..60f, steps = 9, colors = SliderDefaults.colors(thumbColor = Ignition, activeTrackColor = Ignition))
            Pills((3..7).map { it.toString() to "$it yrs" }, years.toString()) { years = it.toInt() }
            if (usable.isNotEmpty()) {
                Text("Bank (published starting rate)", style = MaterialTheme.typography.labelLarge)
                usable.take(6).forEach { b ->
                    Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(12.dp)).background(if (b == bank) Ignition.copy(alpha = 0.12f) else Panel2)
                        .border(1.dp, if (b == bank) Ignition else Line, RoundedCornerShape(12.dp)).clickable { bank = b }.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) { Text(b.bank, fontWeight = FontWeight.SemiBold); Text(b.product, color = Mute, style = MaterialTheme.typography.bodySmall, maxLines = 1) }
                        Text("from ${b.minPct}%", fontWeight = FontWeight.SemiBold)
                        IconButton({ open(b.sourceUrl) }) { Icon(Icons.AutoMirrored.Outlined.OpenInNew, "Bank page", tint = Mute, modifier = Modifier.size(18.dp)) }
                    }
                }
                Text("Your actual rate depends on your credit profile; banks quote it at sanction.", color = Mute, style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}

// ---------------------------------------------------------------- dealer quotes
/** Ask nearby showrooms of this brand for their best on-road price (the same request flow as the website). */
@OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)
@Composable
fun QuoteSheet(variantId: String, variantName: String, city: String, onClose: () -> Unit, vm: BrowseVM) {
    var pin by remember { mutableStateOf("") }
    var finance by remember { mutableStateOf(false) }
    var exchange by remember { mutableStateOf(false) }
    var when_ by remember { mutableStateOf("1 month") }
    var busy by remember { mutableStateOf(false) }
    var done by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()
    androidx.compose.material3.ModalBottomSheet(onDismissRequest = onClose, containerColor = Panel) {
        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 28.dp).navigationBarsPadding(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("Get dealer quotes", style = MaterialTheme.typography.headlineSmall)
            Text("$variantName · $city. Showrooms of this brand near you send their best on-road price with offers and waiting time.", color = Mute)
            if (done != null) { Text(done!!, color = Good, fontWeight = FontWeight.SemiBold); Button(onClose, Modifier.fillMaxWidth()) { Text("Done") }; return@Column }
            androidx.compose.material3.OutlinedTextField(pin, { pin = it.filter(Char::isDigit).take(6) }, Modifier.fillMaxWidth(), singleLine = true,
                label = { Text("Your PIN code (optional)") })
            Text("Buying in", fontWeight = FontWeight.SemiBold)
            Pills(listOf("2 weeks" to "2 weeks", "1 month" to "1 month", "3 months" to "3 months", "Just exploring" to "Just exploring"), when_) { when_ = it }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Pills(listOf("y" to "Need a loan"), if (finance) "y" else "") { finance = !finance }
                Pills(listOf("y" to "Exchange my vehicle"), if (exchange) "y" else "") { exchange = !exchange }
            }
            Text("By sending, you agree that this brand's showrooms near you can see this request and contact you.", color = Mute, style = MaterialTheme.typography.bodySmall)
            Button(onClick = {
                busy = true
                scope.launch {
                    runCatching { vm.api.requestQuote(com.onroad.app.data.QuoteRequestIn(variantId, city, pin.ifBlank { null }, finance, exchange, when_)) }
                        .onSuccess { done = "Request sent. Quotes will appear in My garage as showrooms reply." }
                        .onFailure { done = null; android.util.Log.w("quote", it) }
                    busy = false
                }
            }, Modifier.fillMaxWidth().height(52.dp), enabled = !busy, colors = ButtonDefaults.buttonColors(containerColor = Ignition)) {
                Text(if (busy) "Sending…" else "Send to nearby showrooms", fontWeight = FontWeight.SemiBold)
            }
        }
    }
}
