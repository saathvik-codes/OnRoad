package com.onroad.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
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
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
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
private class Slot(val model: ModelDetail) {
    var variantId by mutableStateOf(model.variants.filter { it.exShowroomInr != null }.minByOrNull { it.exShowroomInr!! }?.id ?: model.variants.firstOrNull()?.id)
    var specs by mutableStateOf<VariantSpecs?>(null)
    val variant get() = model.variants.firstOrNull { it.id == variantId }
}

/** Side-by-side comparison of up to three cars or bikes: on-road price for the user's city, key specs and equipment count. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CompareScreen(onBack: () -> Unit, onModel: (String) -> Unit, vm: BrowseVM = hiltViewModel()) {
    val city by vm.prefs.city.collectAsStateWithLifecycle()
    val slots = remember { mutableStateListOf<Slot>() }
    var picking by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    // (re)load prices when the city changes and specs when a variant changes
    slots.forEach { s -> LaunchedEffect(s.variantId) { s.specs = s.variantId?.let { runCatching { vm.api.specs(it) }.getOrNull() } } }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        ScreenHeader("Compare", "Up to 3 · on-road prices for $city", onBack)
        Row(Modifier.horizontalScroll(rememberScrollState()).padding(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            slots.forEachIndexed { i, s ->
                Column(Modifier.width(170.dp).clip(RoundedCornerShape(20.dp)).background(Panel).border(1.dp, Line, RoundedCornerShape(20.dp)).padding(10.dp)) {
                    Box {
                        AsyncImage(vm.prefs.img(s.variant?.imageUrl ?: s.model.imageUrl, 480), s.model.name, contentScale = ContentScale.Fit,
                            modifier = Modifier.fillMaxWidth().aspectRatio(16 / 10f).clickable { onModel(s.model.id) })
                        IconButton({ slots.removeAt(i) }, Modifier.align(Alignment.TopEnd).size(28.dp)) { Icon(Icons.Outlined.Close, "Remove", tint = Mute) }
                    }
                    Text(s.model.brandName, color = Mute, style = MaterialTheme.typography.labelMedium)
                    Text(s.model.name, style = MaterialTheme.typography.titleMedium, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    var open by remember { mutableStateOf(false) }
                    Box {
                        Text((s.variant?.name ?: "Pick a variant") + "  ▾", color = Ignition, style = MaterialTheme.typography.labelLarge, maxLines = 2,
                            modifier = Modifier.padding(top = 4.dp).clickable { open = true })
                        DropdownMenu(open, { open = false }) {
                            s.model.variants.filter { it.exShowroomInr != null }.sortedBy { it.exShowroomInr }.forEach { v ->
                                DropdownMenuItem(text = { Text("${v.name} · ${lakh(v.exShowroomInr)}") }, onClick = { s.variantId = v.id; open = false })
                            }
                        }
                    }
                }
            }
            if (slots.size < 3) Column(Modifier.width(170.dp).height(210.dp).clip(RoundedCornerShape(20.dp)).border(1.dp, Line, RoundedCornerShape(20.dp))
                .clickable { picking = true }, horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
                Box(Modifier.size(44.dp).clip(RoundedCornerShape(14.dp)).background(Ignition.copy(alpha = 0.14f)), contentAlignment = Alignment.Center) {
                    Icon(Icons.Outlined.Add, null, tint = Ignition)
                }
                Spacer(Modifier.height(8.dp)); Text(if (slots.isEmpty()) "Add a car or bike" else "Add another", color = Mute)
            }
        }
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
        Column(Modifier.padding(horizontal = 16.dp).padding(bottom = 24.dp).height(460.dp)) {
            OutlinedTextField(q, { q = it }, Modifier.fillMaxWidth(), singleLine = true, placeholder = { Text("Search Creta, Nexon, Splendor…") },
                shape = RoundedCornerShape(16.dp))
            Column(Modifier.verticalScroll(rememberScrollState())) {
                hits.filter { h -> slots.none { it.model.id == h.id } }.forEach { h ->
                    Row(Modifier.fillMaxWidth().clickable {
                        picking = false
                        scope.launch {
                            val (b, m) = h.id.split("/", limit = 2)
                            runCatching { vm.api.model(b, m, city, vm.prefs.lat, vm.prefs.lng) }.onSuccess { slots.add(Slot(it)) }
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
    fun row(label: String, values: List<String?>, best: Int? = null) {
        Column(Modifier.fillMaxWidth().padding(horizontal = 16.dp)) {
            Text(label.uppercase(), style = MaterialTheme.typography.labelSmall, color = Mute, modifier = Modifier.padding(top = 12.dp, bottom = 6.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                values.forEachIndexed { i, v ->
                    Text(v ?: "—", fontWeight = if (i == best) FontWeight.Bold else FontWeight.Medium, color = if (i == best) Good else Ink,
                        modifier = Modifier.weight(1f).clip(RoundedCornerShape(12.dp)).background(if (i == best) Good.copy(alpha = 0.08f) else Panel)
                            .padding(10.dp), style = MaterialTheme.typography.bodyMedium)
                }
            }
        }
    }
    val onRoad = slots.map { s -> s.variant?.onroad?.let { it.totalInr - it.refundableInr } }
    row("On-road in $city", onRoad.map { it?.let(::rupees) }, winner(onRoad, lowest = true))
    row("Ex-showroom", slots.map { lakh(it.variant?.exShowroomInr) })
    row("Fuel · gearbox", slots.map { s -> listOfNotNull(s.variant?.fuel, s.variant?.transmission).joinToString(" · ").ifBlank { null } })
    val feats = slots.map { it.specs?.features?.size }
    row("Listed features", feats.map { it?.toString() }, winner(feats.map { it?.takeIf { n -> n > 0 } }, lowest = false))
    val stars = slots.map { s -> s.model.crashTests.mapNotNull { it.adultStars }.maxOrNull() }
    row("Crash rating (adult)", stars.map { it?.let { n -> "$n★ official" } }, winner(stars, lowest = false))
    HEADLINE_SPECS.forEach { (label, rx) ->
        val vals = slots.map { s -> findSpec(s.specs?.specs, rx) }
        if (vals.any { it != null }) row(label, vals)
    }
    Text("Prices from each manufacturer for $city; specs from their official sheets. Green marks the best value in a row.",
        color = Mute, style = MaterialTheme.typography.bodySmall, modifier = Modifier.padding(16.dp))
}
