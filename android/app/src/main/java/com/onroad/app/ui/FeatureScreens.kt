package com.onroad.app.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.ui.graphics.Brush
import androidx.compose.material3.TextButton
import androidx.compose.material.icons.outlined.Tune
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material.icons.outlined.Check
import androidx.compose.material.icons.automirrored.outlined.Sort
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.layout.fillMaxHeight
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
import androidx.compose.material.icons.outlined.WarningAmber
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
fun OfferCard(o: OfferItem, img: (String?) -> String?, modifier: Modifier = Modifier, onOpen: () -> Unit) = Tile(modifier.clickable(onClick = onOpen), pad = 14) {
    Column {
        Row(verticalAlignment = Alignment.CenterVertically) {
            OfferPhoto(o, img, Modifier.width(104.dp).height(72.dp))
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

private val OFFER_SORTS = listOf("benefit" to "Biggest benefit", "ending" to "Ending soon", "brand" to "Brand A–Z", "latest" to "Latest first")
private val BENEFITS = listOf(Triple("u25", "Up to ₹25,000", 0L..25_000L), Triple("25_50", "₹25,000 – ₹50,000", 25_001L..50_000L),
    Triple("50_1l", "₹50,000 – ₹1 lakh", 50_001L..100_000L), Triple("1l", "Above ₹1 lakh", 100_001L..Long.MAX_VALUE))

private data class OfferFilters(val brands: Set<String> = emptySet(), val kinds: Set<String> = emptySet(), val benefit: String? = null,
                                val endingSoon: Boolean = false) {
    val count get() = brands.size + kinds.size + (if (benefit != null) 1 else 0) + (if (endingSoon) 1 else 0)
}

private fun offerDate(s: String?): java.time.LocalDate? = s?.let { Regex("""\d{4}-\d{2}-\d{2}""").find(it)?.value }
    ?.let { runCatching { java.time.LocalDate.parse(it) }.getOrNull() }

private fun kindLabel(k: String?) = when ((k ?: "").lowercase()) {
    "" -> "Other benefits"; "cash", "cash_discount", "discount" -> "Cash discount"; "exchange" -> "Exchange bonus"
    "corporate" -> "Corporate offer"; "finance", "emi", "loan" -> "Finance / EMI"; "loyalty" -> "Loyalty bonus"
    "scrappage" -> "Scrappage bonus"; else -> k!!.replace('_', ' ').replaceFirstChar { it.uppercase() }
}

private fun offerMatches(o: OfferItem, f: OfferFilters, skip: String? = null): Boolean {
    if (skip != "brand" && f.brands.isNotEmpty() && o.brandSlug !in f.brands) return false
    if (skip != "kind" && f.kinds.isNotEmpty() && kindLabel(o.kind) !in f.kinds) return false
    if (skip != "benefit" && f.benefit != null) {
        val r = BENEFITS.first { it.first == f.benefit }.third
        if (o.amountInr == null || o.amountInr !in r) return false
    }
    if (skip != "ending" && f.endingSoon) {
        val d = offerDate(o.validUntil) ?: return false
        if (d.isAfter(java.time.LocalDate.now().plusDays(7))) return false
    }
    return true
}

@OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)
@Composable
fun OffersScreen(onBack: () -> Unit, vm: BrowseVM = hiltViewModel()) {
    val city by vm.prefs.city.collectAsStateWithLifecycle()
    var list by remember { mutableStateOf<List<OfferItem>?>(null) }
    val ctx = LocalContext.current
    var failed by remember { mutableStateOf(false) }
    var tick by remember { mutableIntStateOf(0) }
    var f by remember { mutableStateOf(OfferFilters()) }
    var sort by remember { mutableStateOf("benefit") }
    var sheet by remember { mutableStateOf<String?>(null) }
    LaunchedEffect(city, tick) {
        failed = false; list = null
        runCatching { vm.api.offers(city, 120) }.onSuccess { list = it }.onFailure { failed = true }
    }
    val all = list.orEmpty()
    val brands = all.groupBy { it.brandSlug }.map { (slug, l) -> com.onroad.app.data.Brand(slug, l.first().brandName ?: slug, "/api/logos/$slug", l.size) }
        .sortedByDescending { it.models }
    val shown = list?.filter { offerMatches(it, f) }?.let { l ->
        when (sort) {
            "benefit" -> l.sortedByDescending { it.amountInr ?: 0 }
            "ending" -> l.sortedBy { offerDate(it.validUntil) ?: java.time.LocalDate.MAX }
            "brand" -> l.sortedBy { (it.brandName ?: it.brandSlug).lowercase() }
            else -> l
        }
    }

    Box(Modifier.fillMaxSize()) {
        LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 110.dp)) {
            item {
                ScreenHeader("Offers & festive deals", "Live from manufacturers · $city", onBack)
                // two-wheeler makers don't publish dated offers online; deals are given at the showroom
                Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 4.dp).clip(RoundedCornerShape(14.dp)).background(Panel2).padding(12.dp),
                    verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Outlined.LocalOffer, null, tint = Amber, modifier = Modifier.size(18.dp)); Spacer(Modifier.width(10.dp))
                    Text("Bike and scooter makers don't publish offers online. Open a bike and tap Get dealer quotes to get showroom deals.",
                        color = Mute, style = MaterialTheme.typography.bodySmall)
                }
                if (brands.size > 1) LazyRow(contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 12.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    items(brands, key = { it.slug }) { b -> BrandLogo(b, b.slug in f.brands, vm.prefs.img(b.logo, 200)) { f = f.copy(brands = f.brands.toggle(b.slug)) } }
                }
                val active = buildList<Pair<String, () -> Unit>> {
                    f.brands.forEach { s -> add((brands.firstOrNull { it.slug == s }?.name ?: s) to { f = f.copy(brands = f.brands - s) }) }
                    f.kinds.forEach { k -> add(k to { f = f.copy(kinds = f.kinds - k) }) }
                    f.benefit?.let { id -> add(BENEFITS.first { it.first == id }.second to { f = f.copy(benefit = null) }) }
                    if (f.endingSoon) add("Ending in 7 days" to { f = f.copy(endingSoon = false) })
                }
                if (active.isNotEmpty()) LazyRow(contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 12.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(active, key = { it.first }) { (label, remove) ->
                        Row(Modifier.clip(RoundedCornerShape(50)).background(Ignition.copy(alpha = 0.14f)).border(1.dp, Ignition.copy(alpha = 0.5f), RoundedCornerShape(50))
                            .clickable { remove() }.padding(start = 12.dp, end = 8.dp, top = 7.dp, bottom = 7.dp), verticalAlignment = Alignment.CenterVertically) {
                            Text(label, style = MaterialTheme.typography.labelLarge, color = Ink); Spacer(Modifier.width(4.dp))
                            Icon(Icons.Outlined.Close, "Remove", tint = Ignition, modifier = Modifier.size(15.dp))
                        }
                    }
                    item { Text("Clear all", color = Ignition, style = MaterialTheme.typography.labelLarge,
                        modifier = Modifier.clickable { f = OfferFilters() }.padding(horizontal = 6.dp, vertical = 7.dp)) }
                }
                shown?.let { Text("${it.size} offer${if (it.size == 1) "" else "s"}", style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.padding(start = 16.dp, top = 16.dp, bottom = 4.dp)) }
            }
            val l = shown
            when {
                failed -> item { ErrorState("Couldn't reach OnRoad. Check your connection.") { tick++ } }
                l == null -> item { Box(Modifier.fillMaxWidth().padding(40.dp), contentAlignment = Alignment.Center) { CircularProgressIndicator(color = Ignition) } }
                all.isEmpty() -> item { Text("No manufacturer offers listed for $city right now.", color = Mute, modifier = Modifier.padding(20.dp)) }
                l.isEmpty() -> item {
                    Column(Modifier.fillMaxWidth().padding(28.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("No offer matches all of these.", color = Mute)
                        TextButton({ f = OfferFilters() }) { Text("Clear filters", color = Ignition) }
                    }
                }
                else -> items(l, key = { it.id }) { o ->
                    OfferCard(o, { vm.prefs.img(it, 480) }, Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 6.dp)) {
                        o.sourceUrl?.let { ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(it))) }
                    }
                }
            }
        }
        Row(Modifier.align(Alignment.BottomCenter).fillMaxWidth()
            .background(Brush.verticalGradient(listOf(Color.Transparent, Night.copy(alpha = 0.95f), Night)))
            .navigationBarsPadding().padding(start = 14.dp, end = 14.dp, top = 16.dp, bottom = 10.dp)) {
            Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(50)).background(Panel2).border(1.dp, Line, RoundedCornerShape(50))) {
                BarButton(Icons.AutoMirrored.Outlined.Sort, "Sort", OFFER_SORTS.first { it.first == sort }.second, Modifier.weight(1f)) { sheet = "sort" }
                Box(Modifier.width(1.dp).height(44.dp).background(Line).align(Alignment.CenterVertically))
                BarButton(Icons.Outlined.Tune, "Filters", if (f.count > 0) "${f.count} applied" else "None", Modifier.weight(1f), badge = f.count) { sheet = "filters" }
            }
        }
    }

    if (sheet == "sort") androidx.compose.material3.ModalBottomSheet({ sheet = null }, containerColor = Panel) {
        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 28.dp).navigationBarsPadding()) {
            Text("Sort offers by", style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(bottom = 8.dp))
            OFFER_SORTS.forEach { (k, lab) ->
                Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(14.dp)).clickable { sort = k; sheet = null }.padding(vertical = 14.dp, horizontal = 6.dp),
                    verticalAlignment = Alignment.CenterVertically) {
                    Text(lab, Modifier.weight(1f), fontWeight = if (sort == k) FontWeight.SemiBold else FontWeight.Normal, color = if (sort == k) Ignition else Ink)
                    if (sort == k) Icon(Icons.Outlined.Check, null, tint = Ignition)
                }
            }
        }
    }
    if (sheet == "filters") {
        val state = androidx.compose.material3.rememberModalBottomSheetState(skipPartiallyExpanded = true)
        androidx.compose.material3.ModalBottomSheet({ sheet = null }, sheetState = state, containerColor = Panel) {
            OfferFilterSheet(all, f, brands, { vm.prefs.img(it, 200) }, onChange = { f = it }) { sheet = null }
        }
    }
}

@Composable
private fun OfferFilterSheet(all: List<OfferItem>, f0: OfferFilters, brands: List<com.onroad.app.data.Brand>, logo: (String?) -> String?,
                             onChange: (OfferFilters) -> Unit, onDone: () -> Unit) {
    var f by remember { mutableStateOf(f0) }
    var cat by remember { mutableStateOf("Brand") }
    val cats = listOf("Brand", "Offer type", "Benefit", "Validity")
    fun set(n: OfferFilters) { f = n; onChange(n) }
    fun count(skip: String, test: (OfferItem) -> Boolean) = all.count { offerMatches(it, f, skip) && test(it) }
    val total = all.count { offerMatches(it, f) }
    val kinds = all.map { kindLabel(it.kind) }.distinct().sorted()
    Column(Modifier.fillMaxWidth().fillMaxHeight(0.8f)) {
        Row(Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
            Text("Filter offers", style = MaterialTheme.typography.titleLarge, modifier = Modifier.weight(1f))
            if (f.count > 0) TextButton({ set(OfferFilters()) }) { Text("Clear all", color = Ignition) }
        }
        Row(Modifier.weight(1f)) {
            Column(Modifier.width(112.dp).fillMaxHeight().background(Night)) {
                cats.forEach { c ->
                    val on = when (c) { "Brand" -> f.brands.isNotEmpty(); "Offer type" -> f.kinds.isNotEmpty(); "Benefit" -> f.benefit != null; else -> f.endingSoon }
                    Row(Modifier.fillMaxWidth().background(if (cat == c) Panel else Color.Transparent).clickable { cat = c }, verticalAlignment = Alignment.CenterVertically) {
                        Box(Modifier.width(3.dp).height(48.dp).background(if (cat == c) Ignition else Color.Transparent))
                        Text(c, Modifier.weight(1f).padding(start = 13.dp), fontWeight = if (cat == c) FontWeight.SemiBold else FontWeight.Normal,
                            color = if (cat == c) Ink else Mute, style = MaterialTheme.typography.bodyMedium)
                        if (on) Box(Modifier.padding(end = 10.dp).size(7.dp).clip(CircleShape).background(Ignition))
                    }
                }
            }
            Column(Modifier.weight(1f).fillMaxHeight().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                when (cat) {
                    "Brand" -> FlowRow(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                        brands.forEach { b ->
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                BrandLogo(b, b.slug in f.brands, logo(b.logo)) { set(f.copy(brands = f.brands.toggle(b.slug))) }
                                Text("${count("brand") { it.brandSlug == b.slug }}", style = MaterialTheme.typography.labelSmall, color = Mute)
                            }
                        }
                    }
                    "Offer type" -> kinds.forEach { k -> OptionCard(k, null, count("kind") { kindLabel(it.kind) == k }, k in f.kinds) { set(f.copy(kinds = f.kinds.toggle(k))) } }
                    "Benefit" -> BENEFITS.forEach { (id, lab, r) ->
                        OptionCard(lab, null, count("benefit") { it.amountInr != null && it.amountInr in r }, f.benefit == id, radio = true) {
                            set(f.copy(benefit = if (f.benefit == id) null else id))
                        }
                    }
                    else -> OptionCard("Ending in the next 7 days", "Grab these before they lapse",
                        count("ending") { o -> offerDate(o.validUntil)?.let { !it.isAfter(java.time.LocalDate.now().plusDays(7)) } == true }, f.endingSoon) {
                        set(f.copy(endingSoon = !f.endingSoon))
                    }
                }
            }
        }
        Row(Modifier.fillMaxWidth().background(Panel).padding(horizontal = 16.dp, vertical = 12.dp).navigationBarsPadding(),
            horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text("$total", style = MaterialTheme.typography.titleLarge)
                Text("offers", color = Mute, style = MaterialTheme.typography.bodySmall)
            }
            Button(onDone, Modifier.height(50.dp), enabled = total > 0, colors = ButtonDefaults.buttonColors(containerColor = Ignition)) {
                Text(if (total > 0) "Show offers" else "No matches", fontWeight = FontWeight.SemiBold)
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
