package com.onroad.app.ui

import androidx.compose.material.icons.outlined.KeyboardArrowDown
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Add
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedTextField
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil3.compose.AsyncImage
import com.onroad.app.data.Hit
import com.onroad.app.data.ModelDetail
import com.onroad.app.data.VariantSpecs
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/** One compared vehicle: the model, the chosen variant and that variant's spec sheet. */
private class Slot(first: ModelDetail, var city: String) {
    var model by mutableStateOf(first)
    var variantId by mutableStateOf(first.variants.filter { it.exShowroomInr != null }.minByOrNull { it.exShowroomInr!! }?.id ?: first.variants.firstOrNull()?.id)
    var specs by mutableStateOf<VariantSpecs?>(null)
    val variant get() = model.variants.firstOrNull { it.id == variantId }
}

/** Side-by-side comparison of up to three cars or bikes: on-road price for the user's city, key specs and equipment count. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CompareScreen(onBack: () -> Unit, onModel: (String) -> Unit, preset: List<String> = emptyList(), vm: BrowseVM = hiltViewModel()) {
    val city by vm.prefs.city.collectAsStateWithLifecycle()
    val slots = remember { mutableStateListOf<Slot>() }
    var picking by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    // (re)load prices when the city changes and specs when a variant changes
    slots.forEach { s -> LaunchedEffect(s.variantId) { s.specs = s.variantId?.let { runCatching { vm.api.specs(it) }.getOrNull() } } }
    // opened from "Top picks to compare": load those models straight in
    LaunchedEffect(Unit) {
        if (slots.isEmpty()) preset.forEach { id ->
            val (b, m) = id.split("/", limit = 2)
            runCatching { vm.api.model(b, m, city, vm.prefs.lat, vm.prefs.lng) }.onSuccess { slots.add(Slot(it, city)) }
        }
    }
    LaunchedEffect(city) {
        slots.filter { it.city != city }.forEach { s ->
            val (b, m) = s.model.id.split("/", limit = 2)
            runCatching { vm.api.model(b, m, city, vm.prefs.lat, vm.prefs.lng) }.onSuccess { s.model = it; s.city = city }
        }
    }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        ScreenHeader("Compare", "Up to 3 · on-road prices for $city", onBack)
        if (slots.isEmpty()) Art("hero-compare", Modifier.fillMaxWidth().height(170.dp).padding(horizontal = 16.dp))
        // equal columns, no sideways scrolling: two or three cars always fit the screen
        var pickVariantFor by remember { mutableStateOf<Slot?>(null) }
        Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            slots.forEachIndexed { i, s ->
                Column(Modifier.weight(1f).clip(RoundedCornerShape(14.dp)).background(Panel).border(1.dp, Line, RoundedCornerShape(14.dp)).padding(8.dp)) {
                    Box {
                        AsyncImage(vm.prefs.img(s.variant?.imageUrl ?: s.model.imageUrl, 480), s.model.name, contentScale = ContentScale.Fit,
                            modifier = Modifier.fillMaxWidth().aspectRatio(4 / 3f).clickable { onModel(s.model.id) })
                        IconButton({ slots.removeAt(i) }, Modifier.align(Alignment.TopEnd).size(26.dp)) { Icon(Icons.Outlined.Close, "Remove", tint = Mute) }
                    }
                    Text(s.model.brandName, color = Mute, style = MaterialTheme.typography.labelSmall, maxLines = 1)
                    Text(s.model.name, style = MaterialTheme.typography.titleSmall, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    // the variant is a field that looks tappable: label, value and a chevron, like a form select
                    Column(Modifier.padding(top = 8.dp).fillMaxWidth().clip(Corner).border(1.dp, Line, Corner).clickable { pickVariantFor = s }
                        .padding(horizontal = 8.dp, vertical = 6.dp)) {
                        Text("VARIANT", color = Mute, style = MaterialTheme.typography.labelSmall)
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(s.variant?.name ?: "Choose", style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.SemiBold, maxLines = 2,
                                overflow = TextOverflow.Ellipsis, modifier = Modifier.weight(1f))
                            Icon(Icons.Outlined.KeyboardArrowDown, "Change variant", tint = Ink, modifier = Modifier.size(18.dp))
                        }
                        s.variant?.let { v -> Text(listOfNotNull(v.fuel, v.transmission?.let { t -> if (t.equals("manual", true)) "Manual" else "Automatic" })
                            .joinToString(" · "), color = Mute, style = MaterialTheme.typography.bodySmall, maxLines = 1) }
                    }
                }
            }
            if (slots.size < 3) Column(Modifier.weight(1f).height(if (slots.isEmpty()) 160.dp else 180.dp).clip(RoundedCornerShape(14.dp))
                .border(1.dp, Line, RoundedCornerShape(14.dp)).clickable { picking = true },
                horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
                Icon(Icons.Outlined.Add, null, tint = Ignition)
                Spacer(Modifier.height(6.dp)); Text(if (slots.isEmpty()) "Add a car or bike" else "Add another", color = Mute, style = MaterialTheme.typography.labelLarge)
            }
        }
        pickVariantFor?.let { s -> VariantPicker(s.model.variants, s.variantId, onPick = { s.variantId = it }, onClose = { pickVariantFor = null }) }
        if (slots.size >= 2) {
            Spacer(Modifier.height(18.dp))
            CompareTable(slots, city)
        } else Text("Add at least two to see them side by side.", color = Mute, modifier = Modifier.padding(20.dp))
        Spacer(Modifier.height(24.dp))
    }

    if (picking) ModalBottomSheet({ picking = false }, containerColor = Panel) {
        var q by remember { mutableStateOf("") }
        var hits by remember { mutableStateOf<List<Hit>>(emptyList()) }
        LaunchedEffect(q) { delay(200); hits = if (q.trim().length >= 2) runCatching { vm.api.search(q.trim()) }.getOrDefault(emptyList()) else emptyList() }
        Column(Modifier.padding(horizontal = 16.dp).padding(bottom = 24.dp).height(560.dp)) {
            OutlinedTextField(q, { q = it }, Modifier.fillMaxWidth(), singleLine = true, placeholder = { Text("Search Creta, Nexon, Splendor…") },
                shape = RoundedCornerShape(14.dp))
            Column(Modifier.verticalScroll(rememberScrollState())) {
                if (q.trim().length < 2) TopSearches(city, vm, exclude = slots.map { it.model.id }.toSet(), title = "Most compared in $city") { id, _ ->
                    picking = false
                    scope.launch {
                        val (b, m) = id.split("/", limit = 2)
                        runCatching { vm.api.model(b, m, city, vm.prefs.lat, vm.prefs.lng) }.onSuccess { slots.add(Slot(it, city)) }
                    }
                }
                hits.filter { h -> slots.none { it.model.id == h.id } }.forEach { h ->
                    Row(Modifier.fillMaxWidth().clickable {
                        picking = false
                        scope.launch {
                            val (b, m) = h.id.split("/", limit = 2)
                            runCatching { vm.api.model(b, m, city, vm.prefs.lat, vm.prefs.lng) }.onSuccess { slots.add(Slot(it, city)) }
                        }
                    }.padding(vertical = 14.dp)) {
                        Text("${h.brand} ${h.name}", modifier = Modifier.weight(1f), style = MaterialTheme.typography.titleMedium)
                        Text(lakh(h.fromInr), color = Mute)
                    }
                }
            }
        }
    }
}

@Composable
private fun CompareTable(slots: List<Slot>, city: String) {
    /** index of the single best value, or null when it's a tie or there's nothing to compare */
    fun <T : Comparable<T>> winner(v: List<T?>, lowest: Boolean): Int? {
        val known = v.withIndex().filter { it.value != null }
        if (known.size < 2) return null
        val best = if (lowest) known.minOf { it.value!! } else known.maxOf { it.value!! }
        return known.filter { it.value == best }.singleOrNull()?.index
    }
    @Composable
    fun section(title: String) = Text(title, style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(start = 16.dp, top = 20.dp, bottom = 6.dp))
    @Composable
    fun row(label: String, values: List<String?>, best: Int? = null) {
        Column(Modifier.fillMaxWidth().padding(horizontal = 16.dp)) {
            Text(label, style = MaterialTheme.typography.labelMedium, color = Mute, modifier = Modifier.padding(top = 10.dp, bottom = 4.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                values.forEachIndexed { i, v ->
                    Text(v ?: "—", fontWeight = if (i == best) FontWeight.Bold else FontWeight.Normal, color = if (i == best) Good else Ink,
                        modifier = Modifier.weight(1f), style = MaterialTheme.typography.bodyMedium)
                }
                if (values.size < 3) Spacer(Modifier.weight((3 - values.size).toFloat()))
            }
            androidx.compose.material3.HorizontalDivider(color = Line, modifier = Modifier.padding(top = 10.dp))
        }
    }
    val onRoad = slots.map { s -> s.variant?.onroad?.let { it.totalInr - it.refundableInr } }
    section("Price")
    row("On-road in $city", onRoad.map { it?.let(::rupees) }, winner(onRoad, lowest = true))
    row("Ex-showroom", slots.map { lakh(it.variant?.exShowroomInr) })
    section("Engine & economy")
    row("Fuel · gearbox", slots.map { s -> listOfNotNull(s.variant?.fuel, s.variant?.transmission).joinToString(" · ").ifBlank { null } })
    HEADLINE_SPECS.forEach { (label, rx) ->
        val vals = slots.map { s -> findSpec(s.specs?.specs, rx)?.let { v -> specValue(label, v) } }      // same units and format as the model page
        if (vals.any { it != null }) row(label, vals)
    }
    section("Safety & features")
    val stars = slots.map { s -> s.model.crashTests.mapNotNull { it.adultStars }.maxOrNull() }
    row("Crash rating (adult)", stars.map { it?.let { n -> "$n★ official" } }, winner(stars, lowest = false))
    val feats = slots.map { it.specs?.features?.size }
    row("Listed features", feats.map { it?.toString() }, winner(feats.map { it?.takeIf { n -> n > 0 } }, lowest = false))
    Text("On-road prices for $city. Green marks the better value in a row.",
        color = Mute, style = MaterialTheme.typography.bodySmall, modifier = Modifier.padding(16.dp))
}


/** "60kW@5700 rpm or 81.58PS@5700 rpm", "87 bhp @ 6000 rpm", "88.5 PS" -> "80 bhp @ 5700 rpm": one unit so columns compare. */
internal fun normPower(raw: String): String {
    val t = raw.replace(",", "")
    val rpm = Regex("""(\d{3,5}(?:\s*-\s*\d{3,5})?)\s*rpm""", RegexOption.IGNORE_CASE).find(t)?.groupValues?.get(1)?.replace(" ", "")
    val m = Regex("""(\d+(?:\.\d+)?)\s*(bhp|hp|ps|kw)""", RegexOption.IGNORE_CASE).find(t) ?: return raw
    val n = m.groupValues[1].toDouble()
    val bhp = when (m.groupValues[2].lowercase()) { "kw" -> n * 1.341; "ps" -> n * 0.9863; else -> n }
    return "%.0f bhp".format(bhp) + (rpm?.let { " @ $it rpm" } ?: "")
}

/** "111", "113Nm@4400rpm", "11.5 kgm" -> "113 Nm @ 4400 rpm". A bare number is a maker's Nm figure. */
internal fun normTorque(raw: String): String {
    val t = raw.replace(",", "")
    val rpm = Regex("""(\d{3,5}(?:\s*-\s*\d{3,5})?)\s*rpm""", RegexOption.IGNORE_CASE).find(t)?.groupValues?.get(1)?.replace(" ", "")
    val m = Regex("""(\d+(?:\.\d+)?)\s*(nm|kgm|kg-m)?""", RegexOption.IGNORE_CASE).find(t) ?: return raw
    val n = m.groupValues[1].toDouble()
    val nm = if (m.groupValues[2].lowercase().startsWith("kg")) n * 9.807 else n
    return "%.0f Nm".format(nm) + (rpm?.let { " @ $it rpm" } ?: "")
}
