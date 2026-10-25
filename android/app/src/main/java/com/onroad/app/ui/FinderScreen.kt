package com.onroad.app.ui

import androidx.compose.animation.AnimatedContent
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
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material.icons.outlined.ElectricCar
import androidx.compose.material.icons.outlined.LocalGasStation
import androidx.compose.material.icons.outlined.Tune
import androidx.compose.material.icons.outlined.WarningAmber
import androidx.compose.material.icons.outlined.WorkspacePremium
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.RangeSlider
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.onroad.app.data.Brand
import com.onroad.app.data.Reco
import kotlinx.coroutines.delay
import kotlin.math.roundToLong

/** Everything the buyer asked for. Sets are multi-select; an empty set means "any". */
private data class Ask(
    val bike: Boolean = false,
    val budget: ClosedFloatingPointRange<Float> = 0f..12f,       // on-road, lakh
    val usage: String = "mixed",
    val seats: Int = 0,
    val fuels: Set<String> = emptySet(),
    val gears: Set<String> = emptySet(),
    val bodies: Set<String> = emptySet(),
    val brands: Set<String> = emptySet(),
    val km: Int = 1000,
    val prios: List<String> = listOf("value", "safety"),        // in the order picked: first counts most
) {
    val maxL get() = if (bike) 8f else 80f
    val count get() = (if (seats > 0) 1 else 0) + fuels.size + gears.size + bodies.size + brands.size + (if (km != 1000) 1 else 0)
}

private val USES = listOf("city" to "Mostly city", "mixed" to "City + highway", "highway" to "Long drives")
private val PRIOS = listOf("value" to "Value for money", "safety" to "Safety", "mileage" to "Mileage", "features" to "Features",
    "performance" to "Performance", "popular" to "Popular choice")
private val SEATS = listOf(0 to "Any", 5 to "5 or more", 6 to "6 or more", 7 to "7 or more")

private fun lakh(x: Float) = if (x >= 1f) "₹%.1f L".format(x) else "₹%,d".format((x * 100_000).roundToLong())

private suspend fun ask(vm: BrowseVM, city: String, a: Ask, limit: Int): List<Reco> = vm.api.recommendations(
    city, if (a.bike) "bike" else "car", (a.budget.endInclusive * 100_000).roundToLong(), a.usage, if (a.bike) 0 else a.seats,
    a.fuels.joinToString(",").ifBlank { null }, a.gears.takeIf { it.size == 1 }?.first(), a.km,
    (a.prios.ifEmpty { listOf("value") }).joinToString(","), limit,
    a.bodies.joinToString(",").ifBlank { null }, a.brands.joinToString(",").ifBlank { null },
    (a.budget.start * 100_000).roundToLong().takeIf { it > 0 })

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FinderScreen(onBack: () -> Unit, onModel: (String) -> Unit, vm: BrowseVM = hiltViewModel()) {
    val city by vm.prefs.city.collectAsStateWithLifecycle()
    var a by remember { mutableStateOf(Ask()) }
    var res by remember { mutableStateOf<List<Reco>?>(null) }
    var failed by remember { mutableStateOf(false) }
    var tick by remember { mutableIntStateOf(0) }
    var sheet by remember { mutableStateOf<String?>(null) }
    var brands by remember { mutableStateOf<List<Brand>>(emptyList()) }

    LaunchedEffect(a.bike, city) {
        brands = runCatching { vm.api.brands(city, if (a.bike) "bike" else "car") }.getOrElse { emptyList() }
            .filter { it.models > 0 }.sortedByDescending { it.models }
    }
    // results follow every change; a newer change cancels the older request, so stale picks never show
    LaunchedEffect(a, city, tick) {
        delay(250); failed = false; res = null
        runCatching { ask(vm, city, a, 12) }.onSuccess { res = it }.onFailure { failed = true }
    }

    Box(Modifier.fillMaxSize()) {
        LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 110.dp)) {
            item { ScreenHeader("Find my ${if (a.bike) "bike" else "car"}", "Ranked on official prices for $city, crash tests and specs", onBack) }
            item { Art("hero-finder", androidx.compose.ui.Modifier.fillMaxWidth().height(150.dp).padding(horizontal = 16.dp)) }
            item {
                Column(Modifier.padding(horizontal = 16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Pills(listOf("car" to "Car", "bike" to "Bike / scooter"), if (a.bike) "bike" else "car") { t ->
                        val bike = t == "bike"
                        if (bike != a.bike) a = Ask(bike = bike, budget = 0f..(if (bike) 1.5f else 12f), usage = a.usage, prios = a.prios)
                    }
                    BudgetCard(a) { a = a.copy(budget = it) }
                    LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        items(USES, key = { it.first }) { (k, l) -> ToggleChip(l, a.usage == k) { a = a.copy(usage = k) } }
                    }
                }
            }
            // applied filters, each removable
            val chips = buildList<Pair<String, () -> Unit>> {
                if (a.seats > 0) add("${a.seats}+ seats" to { a = a.copy(seats = 0) })
                a.fuels.forEach { x -> add(x to { a = a.copy(fuels = a.fuels - x) }) }
                a.gears.forEach { x -> add(x to { a = a.copy(gears = a.gears - x) }) }
                a.bodies.forEach { x -> add(x to { a = a.copy(bodies = a.bodies - x) }) }
                a.brands.forEach { x -> add((brands.firstOrNull { it.slug == x }?.name ?: x) to { a = a.copy(brands = a.brands - x) }) }
                if (a.km != 1000) add("${a.km} km/month" to { a = a.copy(km = 1000) })
            }
            if (chips.isNotEmpty()) item {
                LazyRow(Modifier.padding(top = 12.dp), contentPadding = PaddingValues(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(chips, key = { it.first }) { (label, remove) ->
                        Row(Modifier.clip(Corner).background(Ignition.copy(alpha = 0.14f)).border(1.dp, Ignition.copy(alpha = 0.5f), Corner)
                            .clickable { remove() }.padding(start = 12.dp, end = 8.dp, top = 7.dp, bottom = 7.dp), verticalAlignment = Alignment.CenterVertically) {
                            Text(label, style = MaterialTheme.typography.labelLarge, color = Ink); Spacer(Modifier.width(4.dp))
                            Icon(Icons.Outlined.Close, "Remove", tint = Ignition, modifier = Modifier.size(15.dp))
                        }
                    }
                    item { Text("Clear all", color = Ignition, style = MaterialTheme.typography.labelLarge,
                        modifier = Modifier.clickable { a = Ask(bike = a.bike, budget = a.budget, usage = a.usage, prios = a.prios) }.padding(horizontal = 6.dp, vertical = 7.dp)) }
                }
            }
            val r = res
            item {
                Column(Modifier.padding(start = 16.dp, end = 16.dp, top = 18.dp, bottom = 6.dp)) {
                    Text(when {
                        r == null -> "Finding your matches…"
                        r.isEmpty() -> "No matches"
                        r.first().pool > r.size -> "Top ${r.size} of ${r.first().pool} matches"
                        else -> "${r.size} ${if (r.size == 1) "match" else "matches"}"
                    }, style = MaterialTheme.typography.titleMedium)
                    Text("Within ${lakh(a.budget.start).takeIf { a.budget.start > 0 }?.let { "$it – " } ?: "up to "}${lakh(a.budget.endInclusive)} on-road · " +
                        "ranked by ${a.prios.ifEmpty { listOf("value") }.joinToString(", ") { k -> PRIOS.first { it.first == k }.second.lowercase() }}",
                        color = Mute, style = MaterialTheme.typography.bodySmall)
                }
            }
            when {
                failed -> item { ErrorState("Couldn't reach OnRoad. Check your connection.") { tick++ } }
                r == null -> item { Box(Modifier.fillMaxWidth().padding(40.dp), contentAlignment = Alignment.Center) { CircularProgressIndicator(color = Ignition) } }
                r.isEmpty() -> item {
                    Column(Modifier.fillMaxWidth().padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Art("empty-search")
                        Text("Nothing in $city fits all of this.", color = Mute)
                        val more = (a.budget.endInclusive * 1.25f).coerceAtMost(a.maxL)
                        if (more > a.budget.endInclusive) TextButton({ a = a.copy(budget = a.budget.start..more) }) { Text("Raise budget to ${lakh(more)}", color = Ignition) }
                        if (a.budget.start > 0) TextButton({ a = a.copy(budget = 0f..a.budget.endInclusive) }) { Text("Remove the minimum price", color = Ignition) }
                        if (a.count > 0) TextButton({ a = Ask(bike = a.bike, budget = a.budget, usage = a.usage, prios = a.prios) }) { Text("Clear filters", color = Ignition) }
                    }
                }
                else -> itemsIndexed(r, key = { _, x -> x.id }) { i, x -> MatchCard(i, x, a, vm) { onModel(x.id) } }
            }
            if (!a.bike && "Electric" !in a.fuels && r?.isNotEmpty() == true) item {
                Text("Electric cars appear when you pick Electric under Filters → Fuel (they need home or office charging).",
                    color = Mute, style = MaterialTheme.typography.bodySmall, modifier = Modifier.padding(horizontal = 16.dp, vertical = 10.dp))
            }
        }
        // pinned bar, the same pattern as Explore
        Row(Modifier.align(Alignment.BottomCenter).fillMaxWidth()
            .background(Brush.verticalGradient(listOf(Color.Transparent, Night.copy(alpha = 0.95f), Night)))
            .navigationBarsPadding().padding(start = 14.dp, end = 14.dp, top = 16.dp, bottom = 10.dp)) {
            Row(Modifier.fillMaxWidth().clip(Corner).background(Panel2).border(1.dp, Line, Corner)) {
                BarButton(Icons.Outlined.WorkspacePremium, "Priority", a.prios.ifEmpty { listOf("value") }
                    .joinToString(", ") { k -> PRIOS.first { it.first == k }.second.substringBefore(" ") }, Modifier.weight(1f)) { sheet = "prio" }
                Box(Modifier.width(1.dp).height(44.dp).background(Line).align(Alignment.CenterVertically))
                BarButton(Icons.Outlined.Tune, "Filters", if (a.count > 0) "${a.count} applied" else "None", Modifier.weight(1f), badge = a.count) { sheet = "filters" }
            }
        }
    }

    if (sheet == "prio") ModalBottomSheet({ sheet = null }, containerColor = Panel) {
        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 24.dp).navigationBarsPadding(), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("What matters most?", style = MaterialTheme.typography.titleLarge)
            Text("Pick one or more. The first one you pick counts the most.", color = Mute, style = MaterialTheme.typography.bodySmall)
            PRIOS.forEach { (k, l) ->
                val pos = a.prios.indexOf(k)
                Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(if (pos >= 0) Ignition.copy(alpha = 0.12f) else Panel2)
                    .border(1.dp, if (pos >= 0) Ignition else Color.Transparent, RoundedCornerShape(16.dp))
                    .clickable { a = a.copy(prios = if (pos >= 0) a.prios - k else a.prios + k) }.padding(horizontal = 14.dp, vertical = 13.dp),
                    verticalAlignment = Alignment.CenterVertically) {
                    Box(Modifier.size(24.dp).clip(CircleShape).background(if (pos >= 0) Ignition else Color.Transparent)
                        .border(1.5.dp, if (pos >= 0) Ignition else Mute, CircleShape), contentAlignment = Alignment.Center) {
                        if (pos >= 0) Text("${pos + 1}", color = Color.White, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold)
                    }
                    Spacer(Modifier.width(12.dp))
                    Text(l, Modifier.weight(1f), fontWeight = FontWeight.SemiBold)
                }
            }
            Button({ sheet = null }, Modifier.fillMaxWidth().height(50.dp), colors = ButtonDefaults.buttonColors(containerColor = Ignition), shape = Corner) {
                Text("Done", fontWeight = FontWeight.SemiBold)
            }
        }
    }
    if (sheet == "filters") {
        val state = rememberModalBottomSheetState(skipPartiallyExpanded = true)
        ModalBottomSheet({ sheet = null }, sheetState = state, containerColor = Panel) {
            FinderFilters(a, brands, city, vm, { vm.prefs.img(it, 200) }, onApply = { a = it; sheet = null })
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun BudgetCard(a: Ask, onChange: (ClosedFloatingPointRange<Float>) -> Unit) = Tile(Modifier.fillMaxWidth(), pad = 16) {
    Column {
        Text("ON-ROAD BUDGET", color = Mute, style = MaterialTheme.typography.labelSmall)
        Text(if (a.budget.start > 0f) "${lakh(a.budget.start)} – ${lakh(a.budget.endInclusive)}" else "Up to ${lakh(a.budget.endInclusive)}",
            style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        val step = if (a.bike) 0.1f else 0.5f
        RangeSlider(a.budget, { v ->
            // snap to steps and keep a sensible gap, so the range never collapses to nothing
            val lo = (v.start / step).roundToLong() * step
            val hi = ((v.endInclusive / step).roundToLong() * step).coerceAtLeast(lo + step).coerceIn(step, a.maxL)
            onChange(lo.coerceAtMost(hi - step).coerceAtLeast(0f)..hi)
        }, valueRange = 0f..a.maxL, colors = SliderDefaults.colors(thumbColor = Ignition, activeTrackColor = Ignition))
        Text("Includes road tax, registration and insurance for your city", color = Mute, style = MaterialTheme.typography.bodySmall)
    }
}

@Composable
private fun ToggleChip(label: String, on: Boolean, onClick: () -> Unit) = Text(label, style = MaterialTheme.typography.labelLarge,
    color = if (on) Color.White else Mute, fontWeight = if (on) FontWeight.SemiBold else FontWeight.Normal,
    modifier = Modifier.clip(Corner).background(if (on) Ignition else Panel2).clickable(onClick = onClick)
        .padding(horizontal = 14.dp, vertical = 9.dp))

@Composable
private fun MatchCard(i: Int, x: Reco, a: Ask, vm: BrowseVM, onOpen: () -> Unit) = Tile(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 6.dp).clickable(onClick = onOpen), pad = 14) {
    Column {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box {
                VehicleImage(vm.prefs.img(x.imageUrl, 480), x.name, Modifier.width(118.dp).aspectRatio(16 / 10f))
                Text("#${i + 1}", color = Color.White, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold,
                    modifier = Modifier.clip(RoundedCornerShape(bottomEnd = 10.dp, topStart = 10.dp)).background(if (i == 0) Ignition else Color.Black.copy(alpha = 0.6f))
                        .padding(horizontal = 8.dp, vertical = 3.dp))
            }
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(x.brand, color = Mute, style = MaterialTheme.typography.labelMedium, maxLines = 1)
                Text(x.name, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                x.variant?.let { Text(it, color = Mute, style = MaterialTheme.typography.bodySmall, maxLines = 1, overflow = TextOverflow.Ellipsis) }
                x.fromInr?.let { Text(rupees(it), style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold) }
            }
        }
        // match strength
        Row(Modifier.padding(top = 10.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.weight(1f).height(6.dp).clip(RoundedCornerShape(50)).background(Panel2)) {
                Box(Modifier.fillMaxWidth(x.matchScore.coerceIn(0, 100) / 100f).fillMaxHeight().clip(RoundedCornerShape(50))
                    .background(if (x.matchScore >= 80) Good else if (x.matchScore >= 65) Ignition else Amber))
            }
            Spacer(Modifier.width(10.dp))
            Text("${x.matchScore}% match", style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.SemiBold)
        }
        Row(Modifier.padding(top = 8.dp), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            listOfNotNull(x.fuels, x.transmission, x.bodyType).distinct().forEach { Chip(it, Electric) }
            x.crashStars?.let { s -> Chip("$s★ NCAP", if (s >= 4) Good else Amber) }
        }
        val under = x.fromInr?.let { (a.budget.endInclusive * 100_000).roundToLong() - it }
        Column(Modifier.padding(top = 8.dp)) {
            if (under != null && under >= 1000) Reason("₹${"%,d".format(under / 1000)}k under your budget", Icons.Outlined.CheckCircle, Good)
            x.reasons.filterNot { it.startsWith("On-road") }.take(3).forEach { Reason(it, Icons.Outlined.CheckCircle, Good) }
            x.warnings.forEach { Reason(it, Icons.Outlined.WarningAmber, Amber, Amber) }
        }
    }
}

@Composable
private fun Reason(text: String, icon: androidx.compose.ui.graphics.vector.ImageVector, tint: Color, color: Color = Ink) =
    Row(Modifier.padding(vertical = 2.dp)) {
        Icon(icon, null, tint = tint, modifier = Modifier.size(16.dp).padding(top = 2.dp)); Spacer(Modifier.width(6.dp))
        Text(text, style = MaterialTheme.typography.bodyMedium, color = color)
    }

/** Two-pane filter sheet like Explore's; the footer counts the matches for the draft live before applying. */
@Composable
private fun FinderFilters(a0: Ask, brands: List<Brand>, city: String, vm: BrowseVM, logo: (String?) -> String?, onApply: (Ask) -> Unit) {
    var a by remember { mutableStateOf(a0) }
    val cats = (if (a.bike) emptyList() else listOf("Seats")) + listOf("Fuel") + (if (a.bike) emptyList() else listOf("Gearbox")) +
        listOf("Body type", "Brand", "Running")
    var cat by remember { mutableStateOf(cats.first()) }
    var pool by remember { mutableStateOf<Int?>(null) }
    LaunchedEffect(a) {
        pool = null; delay(300)
        pool = runCatching { ask(vm, city, a, 1).firstOrNull()?.pool ?: 0 }.getOrNull()
    }
    Column(Modifier.fillMaxWidth().fillMaxHeight(0.82f)) {
        Row(Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
            Text("Filters", style = MaterialTheme.typography.titleLarge, modifier = Modifier.weight(1f))
            if (a.count > 0) TextButton({ a = a.copy(seats = 0, fuels = emptySet(), gears = emptySet(), bodies = emptySet(), brands = emptySet(), km = 1000) }) {
                Text("Clear all", color = Ignition)
            }
        }
        Row(Modifier.weight(1f)) {
            Column(Modifier.width(112.dp).fillMaxHeight().background(Night)) {
                cats.forEach { c ->
                    val active = when (c) { "Seats" -> a.seats > 0; "Fuel" -> a.fuels.isNotEmpty(); "Gearbox" -> a.gears.isNotEmpty()
                        "Body type" -> a.bodies.isNotEmpty(); "Brand" -> a.brands.isNotEmpty(); else -> a.km != 1000 }
                    Row(Modifier.fillMaxWidth().background(if (cat == c) Panel else Color.Transparent).clickable { cat = c }, verticalAlignment = Alignment.CenterVertically) {
                        Box(Modifier.width(3.dp).height(48.dp).background(if (cat == c) Ignition else Color.Transparent))
                        Text(c, Modifier.weight(1f).padding(start = 13.dp), fontWeight = if (cat == c) FontWeight.SemiBold else FontWeight.Normal,
                            color = if (cat == c) Ink else Mute, style = MaterialTheme.typography.bodyMedium)
                        if (active) Box(Modifier.padding(end = 10.dp).size(7.dp).clip(CircleShape).background(Ignition))
                    }
                }
            }
            AnimatedContent(cat, Modifier.weight(1f).fillMaxHeight(), label = "cat") { c ->
                Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    when (c) {
                        "Seats" -> SEATS.forEach { (n, l) -> OptionCard(l, if (n >= 6) "MUVs and 3-row SUVs" else null, null, a.seats == n, radio = true) { a = a.copy(seats = n) } }
                        "Fuel" -> (if (a.bike) BIKE_FUELS else CAR_FUELS).forEach { x ->
                            OptionCard(x, when (x) { "Hybrid" -> "Strong hybrids"; "Electric" -> if (a.bike) null else "Needs home or office charging"; else -> null },
                                null, x in a.fuels, icon = if (x == "Electric") Icons.Outlined.ElectricCar else Icons.Outlined.LocalGasStation) { a = a.copy(fuels = a.fuels.toggle(x)) }
                        }
                        "Gearbox" -> GEARBOX.forEach { g ->
                            OptionCard(g, if (g == "Automatic") "AMT, CVT, DCT, torque converter, EV" else null, null, g in a.gears) { a = a.copy(gears = a.gears.toggle(g)) }
                        }
                        "Body type" -> (if (a.bike) BIKE_BODIES else CAR_BODIES).forEach { b -> OptionCard(b, null, null, b in a.bodies) { a = a.copy(bodies = a.bodies.toggle(b)) } }
                        "Brand" -> FlowRow(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                            brands.forEach { b -> BrandLogo(b, b.slug in a.brands, logo(b.logo)) { a = a.copy(brands = a.brands.toggle(b.slug)) } }
                        }
                        else -> Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            Text("${a.km} km a month", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                            Slider(a.km.toFloat(), { a = a.copy(km = (it / 100).toInt() * 100) }, valueRange = 200f..4000f, steps = 37,
                                colors = SliderDefaults.colors(thumbColor = Ignition, activeTrackColor = Ignition))
                            Text("Heavy running favours diesel, CNG and electric in the ranking.", color = Mute, style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
            }
        }
        Row(Modifier.fillMaxWidth().background(Panel).padding(horizontal = 16.dp, vertical = 12.dp).navigationBarsPadding(),
            horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text(pool?.toString() ?: "…", style = MaterialTheme.typography.titleLarge)
                Text("matching models", color = Mute, style = MaterialTheme.typography.bodySmall)
            }
            Button({ onApply(a) }, Modifier.height(50.dp), enabled = pool != 0, colors = ButtonDefaults.buttonColors(containerColor = Ignition), shape = Corner) {
                Text(if (pool == 0) "No matches" else "Show matches", fontWeight = FontWeight.SemiBold)
            }
        }
    }
}
