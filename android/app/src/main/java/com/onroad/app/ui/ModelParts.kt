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
        Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("insurance" to "Insurance", "rta" to "Registration", "accessories" to "Accessories", "updates" to "Updates").forEach { (k, l) -> Chip2(l, part == k) { part = k } }
        }
        if (o == null) { Text(if (failed) "Couldn't load this right now." else "Loading…", color = Mute); return@Column }
        when (part) {
            "insurance" -> {
                Amounts(o.insurance.lines)
                o.insurance.tips.forEach { Text("• $it", color = Mute, style = MaterialTheme.typography.bodySmall) }
                Text("Get your own quotes", style = MaterialTheme.typography.titleMedium)
                o.insurance.insurers.chunked(2).forEach { pair ->
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        pair.forEach { ins -> InsurerCard(ins, Modifier.weight(1f)) { open(ins.url) } }
                        if (pair.size == 1) Spacer(Modifier.weight(1f))
                    }
                }
                Text("Compare many insurers at once", style = MaterialTheme.typography.titleSmall)
                LinkRow(o.insurance.compare.map { (it.name ?: it.title ?: "") to it.url }, open)
                Text("* As stated on each insurer's website. " + o.insurance.disclosure, color = Mute, style = MaterialTheme.typography.bodySmall)
            }
            "rta" -> {
                Text("Registration in ${o.rta.state}", style = MaterialTheme.typography.titleMedium)
                Amounts(o.rta.charges)
                o.rta.ev?.takeIf { it.lifeTaxExempt == true }?.let {
                    Text("Electric vehicles pay no road tax in ${o.rta.state}${it.validTo?.let { d -> " until $d" } ?: ""}.", color = Good)
                }
                Text("How it works", style = MaterialTheme.typography.titleMedium)
                o.rta.steps.forEachIndexed { i, s -> Text("${i + 1}. $s", color = Mute, style = MaterialTheme.typography.bodySmall) }
                Text("Charges a dealer cannot add", style = MaterialTheme.typography.titleMedium)
                o.rta.notAllowed.forEach { Text("• ${it.item}: ${it.status}", color = Mute, style = MaterialTheme.typography.bodySmall) }
                LinkRow((o.rta.links + o.rta.sources).map { (it.title ?: it.name ?: "") to it.url }, open)
            }
            "accessories" -> {
                if (o.accessories.items.isNotEmpty()) {
                    Text("${o.accessories.items.size} genuine accessories, ${brand}'s list prices", color = Mute, style = MaterialTheme.typography.bodySmall)
                    o.accessories.items.chunked(2).forEach { pair ->
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                            pair.forEach { a -> AccessoryCard(a, Modifier.weight(1f)) }
                            if (pair.size == 1) Spacer(Modifier.weight(1f))
                        }
                    }
                }
                o.accessories.official?.let { LinkRow(listOf("$brand accessories store" to it.url), open) }
                    ?: Text("$brand doesn't publish an accessory catalogue online. Ask the dealer for the itemised price list.", color = Mute)
                o.accessories.advice.forEach { Text("• $it", color = Mute, style = MaterialTheme.typography.bodySmall) }
            }
            else -> {
                if (o.updates.isEmpty()) Text("No price changes or new offers in the last four months.", color = Mute)
                o.updates.forEach { u ->
                    Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(14.dp)).background(Panel).border(1.dp, Line, RoundedCornerShape(14.dp)).padding(12.dp)) {
                        Text(u.title, style = MaterialTheme.typography.titleSmall)
                        Text("${u.date} · ${u.detail}", color = Mute, style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }
    }
}

@Composable
private fun InsurerCard(i: com.onroad.app.data.Insurer, modifier: Modifier, onClick: () -> Unit) {
    val vm: BrowseVM = androidx.hilt.navigation.compose.hiltViewModel()
    Column(modifier.clip(RoundedCornerShape(14.dp)).background(Panel).border(1.dp, Line, RoundedCornerShape(14.dp)).clickable(onClick = onClick).padding(10.dp)) {
        androidx.compose.foundation.layout.Box(Modifier.fillMaxWidth().height(44.dp).clip(RoundedCornerShape(10.dp))
            .background(if (i.logoDark) Color(0xFF1B1F2A) else Color.White).padding(6.dp), contentAlignment = Alignment.Center) {
            if (i.logoUrl != null) coil3.compose.AsyncImage(vm.prefs.img(i.logoUrl, 300), i.name, modifier = Modifier.fillMaxWidth())
            else Text(i.name, color = Color(0xFF1B1F2A), fontWeight = FontWeight.Bold)
        }
        Spacer(Modifier.height(6.dp))
        Text(i.name, style = MaterialTheme.typography.titleSmall)
        Text(i.garages?.let { "$it cashless garages*" } ?: "Get a quote", color = Mute, style = MaterialTheme.typography.bodySmall)
    }
}

@Composable
private fun AccessoryCard(a: com.onroad.app.data.Accessory, modifier: Modifier) {
    Column(modifier.clip(RoundedCornerShape(14.dp)).background(Panel).border(1.dp, Line, RoundedCornerShape(14.dp))) {
        coil3.compose.AsyncImage(a.imageUrl, a.name, contentScale = androidx.compose.ui.layout.ContentScale.Crop,
            modifier = Modifier.fillMaxWidth().height(110.dp).background(Color.White))
        Column(Modifier.padding(10.dp)) {
            a.category?.let { Text(it.uppercase(), color = Mute, style = MaterialTheme.typography.labelSmall) }
            Text(a.name, style = MaterialTheme.typography.titleSmall, maxLines = 2, overflow = TextOverflow.Ellipsis)
            a.priceInr?.let { Text(rupees(it), fontWeight = FontWeight.SemiBold, color = Ink) }
        }
    }
}

@Composable
private fun Amounts(lines: List<OwnLine>) = Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(Panel)
    .border(1.dp, Line, RoundedCornerShape(16.dp))) {
    lines.forEachIndexed { i, l ->
        if (i > 0) HorizontalDivider(color = Line)
        Row(Modifier.fillMaxWidth().padding(12.dp)) {
            Column(Modifier.weight(1f)) {
                Text(l.label, style = MaterialTheme.typography.titleSmall)
                Text(l.basis, color = Mute, style = MaterialTheme.typography.bodySmall, maxLines = 3)
            }
            Spacer(Modifier.width(8.dp))
            Text(l.amountInr?.let { rupees(it) } ?: "—", fontWeight = FontWeight.SemiBold)
        }
    }
}

@Composable
private fun LinkRow(links: List<Pair<String, String>>, open: (String) -> Unit) = Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
    links.filter { it.first.isNotBlank() }.forEach { (label, url) ->
        Text("$label  ↗", color = Electric, style = MaterialTheme.typography.labelLarge, modifier = Modifier.clickable { open(url) }.padding(vertical = 4.dp))
    }
}
