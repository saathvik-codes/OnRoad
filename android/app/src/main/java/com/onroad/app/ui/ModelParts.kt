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
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.onroad.app.data.OwnLine
import com.onroad.app.data.Ownership
import com.onroad.app.data.Variant

/** The chosen variant as a card; tapping it opens the full picker. */
@Composable
fun VariantCard(v: Variant?, count: Int, onClick: () -> Unit) {
    Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp).clip(RoundedCornerShape(16.dp)).background(Panel)
        .border(1.dp, Line, RoundedCornerShape(16.dp)).clickable(onClick = onClick).padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) {
            Text("VARIANT", style = MaterialTheme.typography.labelSmall, color = Mute)
            Text(v?.name ?: "Choose a variant", style = MaterialTheme.typography.titleMedium, maxLines = 1, overflow = TextOverflow.Ellipsis)
            Text(listOfNotNull(v?.fuel, v?.transmission, v?.onroad?.let { "on-road ${lakh(it.totalInr - it.refundableInr)}" })
                .joinToString(" · "), color = Mute, style = MaterialTheme.typography.bodySmall, maxLines = 1)
        }
        Text("Change ($count)", color = Ignition, fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.labelLarge)
    }
}

/** Every variant, filterable by fuel and gearbox, searchable, grouped by fuel and sorted by price. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun VariantPicker(variants: List<Variant>, selected: String?, onPick: (String) -> Unit, onClose: () -> Unit) {
    val state = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    var fuel by remember { mutableStateOf<String?>(null) }
    var gear by remember { mutableStateOf<String?>(null) }
    var q by remember { mutableStateOf("") }
    val fuels = variants.mapNotNull { it.fuel }.distinct()
    val auto = { v: Variant -> !(v.transmission ?: "").equals("manual", true) }
    val shown = variants.filter { v ->
        (fuel == null || v.fuel == fuel) && (gear == null || (gear == "Automatic") == auto(v)) &&
            (q.isBlank() || v.name.contains(q.trim(), true))
    }.sortedBy { it.exShowroomInr ?: Long.MAX_VALUE }
    val cheapest = variants.mapNotNull { it.exShowroomInr }.minOrNull()
    ModalBottomSheet(onDismissRequest = onClose, sheetState = state, containerColor = Panel) {
        Column(Modifier.padding(horizontal = 16.dp)) {
            Text("Choose a variant", style = MaterialTheme.typography.titleLarge)
            Text("${variants.size} variants · prices for your city", color = Mute, style = MaterialTheme.typography.bodySmall)
            Spacer(Modifier.height(12.dp))
            if (variants.size > 8) OutlinedTextField(q, { q = it }, Modifier.fillMaxWidth(), singleLine = true, shape = Corner,
                placeholder = { Text("Search, e.g. ZXi, AMT") })
            Row(Modifier.horizontalScroll(rememberScrollState()).padding(vertical = 10.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                if (fuels.size > 1) (listOf<String?>(null) + fuels).forEach { f ->
                    Chip2(f ?: "All fuels", fuel == f) { fuel = f }
                }
                if (variants.any(auto) && variants.any { !auto(it) }) listOf<String?>(null, "Manual", "Automatic").forEach { g ->
                    Chip2(g ?: "Any gearbox", gear == g) { gear = g }
                }
            }
        }
        LazyColumn(Modifier.heightIn(max = 560.dp).navigationBarsPadding(), contentPadding = PaddingValues(bottom = 16.dp)) {
            val groups = shown.groupBy { it.fuel ?: "Other" }
            groups.forEach { (f, list) ->
                if (groups.size > 1) item(key = "h$f") {
                    Text(f.uppercase(), style = MaterialTheme.typography.labelSmall, color = Mute, modifier = Modifier.padding(start = 16.dp, top = 12.dp, bottom = 4.dp))
                }
                items(list, key = { it.id }) { v ->
                    val on = v.id == selected
                    Row(Modifier.fillMaxWidth().clickable { onPick(v.id); onClose() }
                        .background(if (on) Ignition.copy(alpha = 0.08f) else Color.Transparent).padding(horizontal = 16.dp, vertical = 12.dp),
                        verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text(v.name, style = MaterialTheme.typography.titleSmall, color = if (on) Ignition else Ink, maxLines = 2)
                            Text(listOfNotNull(v.transmission, if (v.exShowroomInr == cheapest) "Lowest price" else null).joinToString(" · "),
                                color = Mute, style = MaterialTheme.typography.bodySmall)
                        }
                        Column(horizontalAlignment = Alignment.End) {
                            Text(lakh(v.exShowroomInr), fontWeight = FontWeight.SemiBold)
                            v.onroad?.let { Text("on-road ${lakh(it.totalInr - it.refundableInr)}", color = Mute, style = MaterialTheme.typography.bodySmall) }
                        }
                    }
                    HorizontalDivider(color = Line)
                }
            }
            if (shown.isEmpty()) item { Text("No variant matches.", color = Mute, modifier = Modifier.padding(16.dp)) }
        }
    }
}

@Composable
private fun Chip2(label: String, on: Boolean, onClick: () -> Unit) = Text(label, style = MaterialTheme.typography.labelLarge,
    color = if (on) Color.White else Ink,
    modifier = Modifier.clip(Corner).background(if (on) Ignition else Panel2).clickable(onClick = onClick).padding(horizontal = 12.dp, vertical = 7.dp))

/** Insurance, registration (RTA), accessories and recent changes for the chosen variant in the buyer's city. */
@Composable
fun OwnershipTab(o: Ownership?, brand: String, failed: Boolean) {
    val ctx = LocalContext.current
    val open = { u: String -> ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(u))) }
    var part by remember { mutableStateOf("insurance") }
    Column(Modifier.padding(horizontal = 16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(Modifier.fillMaxWidth().clip(Corner).background(Panel2).padding(4.dp)) {
            listOf("insurance" to "Insurance", "rta" to "Registration", "accessories" to "Accessories").forEach { (k, l) ->
                Text(l, textAlign = androidx.compose.ui.text.style.TextAlign.Center, style = MaterialTheme.typography.labelLarge,
                    fontWeight = if (part == k) FontWeight.SemiBold else FontWeight.Normal, color = if (part == k) Ink else Mute,
                    modifier = Modifier.weight(1f).clip(Corner).background(if (part == k) Panel else Color.Transparent)
                        .clickable { part = k }.padding(vertical = 9.dp))
            }
        }
        if (o == null) { Text(if (failed) "Couldn't load this right now." else "Loading…", color = Mute); return@Column }
        when (part) {
            "insurance" -> {
                val total = o.insurance.lines.mapNotNull { it.amountInr }.sum()
                Headline("Insurance at purchase", if (total > 0) rupees(total) else "",
                    "Third-party cover is fixed by law; own-damage is an estimate. Compare before you pay the dealer.")
                Breakdown(o.insurance.lines)
                Text("Get quotes", style = MaterialTheme.typography.titleSmall)
                o.insurance.insurers.chunked(3).forEach { row ->
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        row.forEach { ins -> InsurerCard(ins, Modifier.weight(1f)) { open(ins.url) } }
                        repeat(3 - row.size) { Spacer(Modifier.weight(1f)) }
                    }
                }
                Expandable("Ways to pay less") { o.insurance.tips.forEach { Bullet(it) } }
                Text("Garage counts as stated by each insurer. OnRoad has no tie-up with any insurer.", color = Mute,
                    style = MaterialTheme.typography.labelSmall)
            }
            "rta" -> {
                val total = o.rta.charges.mapNotNull { it.amountInr }.sum()
                Headline("Registration in ${o.rta.state}", if (total > 0) rupees(total) else "", "Road tax and fees, paid once to the state")
                Breakdown(o.rta.charges)
                o.rta.ev?.takeIf { it.lifeTaxExempt == true }?.let {
                    Text("Electric vehicles pay no road tax in ${o.rta.state}${it.validTo?.let { d -> " until $d" } ?: ""}.", color = Good,
                        style = MaterialTheme.typography.bodySmall)
                }
                Expandable("How registration works") { o.rta.steps.forEachIndexed { i, s -> Bullet("${i + 1}. $s", numbered = true) } }
                Expandable("Charges a dealer can't add (${o.rta.notAllowed.size})") { o.rta.notAllowed.forEach { Bullet(it.item) } }
                Expandable("Official sources") { LinkRow((o.rta.links + o.rta.sources).map { (it.title ?: it.name ?: "") to it.url }, open) }
            }
            else -> {
                val items = o.accessories.items
                if (items.isNotEmpty()) {
                    var all by remember { mutableStateOf(false) }
                    Headline("Genuine accessories", "${items.size} items", "$brand's own list prices; fitting may cost extra")
                    (if (all) items else items.take(6)).chunked(2).forEach { pair ->
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                            pair.forEach { a -> AccessoryCard(a, Modifier.weight(1f)) }
                            if (pair.size == 1) Spacer(Modifier.weight(1f))
                        }
                    }
                    if (items.size > 6) Text(if (all) "Show fewer" else "Show all ${items.size}", color = Ignition, fontWeight = FontWeight.SemiBold,
                        modifier = Modifier.clickable { all = !all }.padding(vertical = 6.dp))
                } else {
                    Headline("Genuine accessories", "", "$brand doesn't publish an accessory price list online. Ask the dealer for theirs.")
                    o.accessories.official?.let { LinkRow(listOf("$brand accessories store" to it.url), open) }
                }
                Expandable("Before you buy accessories") { o.accessories.advice.forEach { Bullet(it) } }
            }
        }
    }
}

@Composable
private fun Headline(title: String, value: String, sub: String) = Column {
    Text(title, color = Mute, style = MaterialTheme.typography.labelMedium)
    if (value.isNotBlank()) Text(value, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
    Text(sub, color = Mute, style = MaterialTheme.typography.bodySmall)
}

/** Amounts as compact rows; tap a row to see how it was worked out. */
@Composable
private fun Breakdown(lines: List<OwnLine>) = Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(14.dp)).background(Panel)
    .border(1.dp, Line, RoundedCornerShape(14.dp))) {
    lines.forEachIndexed { i, l ->
        var why by remember(l.label) { mutableStateOf(false) }
        if (i > 0) HorizontalDivider(color = Line)
        Column(Modifier.fillMaxWidth().clickable { why = !why }.padding(horizontal = 12.dp, vertical = 10.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(l.label.removePrefix("Insurance: ").replaceFirstChar { it.uppercase() }, style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.weight(1f))
                Text(l.amountInr?.let { rupees(it) } ?: "—", fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.bodyMedium)
            }
            if (why && l.basis.isNotBlank()) Text(l.basis, color = Mute, style = MaterialTheme.typography.bodySmall, modifier = Modifier.padding(top = 4.dp))
        }
    }
}

@Composable
private fun Expandable(title: String, content: @Composable () -> Unit) {
    var open by remember(title) { mutableStateOf(false) }
    Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(14.dp)).border(1.dp, Line, RoundedCornerShape(14.dp))) {
        Row(Modifier.fillMaxWidth().clickable { open = !open }.padding(horizontal = 12.dp, vertical = 12.dp), verticalAlignment = Alignment.CenterVertically) {
            Text(title, style = MaterialTheme.typography.titleSmall, modifier = Modifier.weight(1f))
            Text(if (open) "Hide" else "Show", color = Ignition, style = MaterialTheme.typography.labelLarge)
        }
        if (open) Column(Modifier.padding(start = 12.dp, end = 12.dp, bottom = 12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) { content() }
    }
}

@Composable
private fun Bullet(text: String, numbered: Boolean = false) =
    Text(if (numbered) text else "•  $text", color = Mute, style = MaterialTheme.typography.bodySmall)

@Composable
private fun InsurerCard(i: com.onroad.app.data.Insurer, modifier: Modifier, onClick: () -> Unit) {
    val vm: BrowseVM = androidx.hilt.navigation.compose.hiltViewModel()
    Column(modifier.clip(RoundedCornerShape(12.dp)).background(Panel).border(1.dp, Line, RoundedCornerShape(12.dp)).clickable(onClick = onClick).padding(8.dp),
        horizontalAlignment = Alignment.CenterHorizontally) {
        androidx.compose.foundation.layout.Box(Modifier.fillMaxWidth().height(36.dp).clip(RoundedCornerShape(8.dp))
            .background(if (i.logoDark) Color(0xFF1B1F2A) else Color.White).padding(5.dp), contentAlignment = Alignment.Center) {
            if (i.logoUrl != null) coil3.compose.AsyncImage(vm.prefs.img(i.logoUrl, 300), i.name, modifier = Modifier.fillMaxWidth())
            else Text(i.name, color = Color(0xFF1B1F2A), fontWeight = FontWeight.Bold, style = MaterialTheme.typography.labelMedium)
        }
        Spacer(Modifier.height(4.dp))
        Text(i.garages?.let { "$it garages" } ?: i.name, color = Mute, style = MaterialTheme.typography.labelSmall, maxLines = 1)
    }
}

@Composable
private fun AccessoryCard(a: com.onroad.app.data.Accessory, modifier: Modifier) {
    Column(modifier.clip(RoundedCornerShape(14.dp)).background(Panel).border(1.dp, Line, RoundedCornerShape(14.dp))) {
        coil3.compose.AsyncImage(a.imageUrl, a.name, contentScale = androidx.compose.ui.layout.ContentScale.Crop,
            modifier = Modifier.fillMaxWidth().height(100.dp).background(Color.White))
        Column(Modifier.padding(10.dp)) {
            Text(a.name, style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.SemiBold, maxLines = 2, overflow = TextOverflow.Ellipsis)
            a.priceInr?.let { Text(rupees(it), style = MaterialTheme.typography.bodySmall, color = Ink) }
        }
    }
}

@Composable
private fun LinkRow(links: List<Pair<String, String>>, open: (String) -> Unit) = Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
    links.filter { it.first.isNotBlank() }.forEach { (label, url) ->
        Text("$label  ↗", color = Electric, style = MaterialTheme.typography.bodySmall, modifier = Modifier.clickable { open(url) }.padding(vertical = 3.dp))
    }
}
