package com.onroad.app.ui

import androidx.compose.animation.animateContentSize
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.AcUnit
import androidx.compose.material.icons.outlined.Check
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material.icons.outlined.DirectionsCar
import androidx.compose.material.icons.outlined.KeyboardArrowDown
import androidx.compose.material.icons.outlined.KeyboardArrowUp
import androidx.compose.material.icons.outlined.Lightbulb
import androidx.compose.material.icons.outlined.MoreHoriz
import androidx.compose.material.icons.outlined.Shield
import androidx.compose.material.icons.outlined.Tv
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil3.compose.AsyncImage
import com.onroad.app.data.Feature
import com.onroad.app.data.VariantSpecs

private data class Cat(val name: String, val icon: ImageVector, val tint: Color, val words: List<String>)

private val CATS = listOf(
    Cat("Safety", Icons.Outlined.Shield, Good, listOf("airbag", "abs", "ebd", "esc", "esp", "isofix", "camera", "sensor", "tpms", "hill", "brake", "adas",
        "seatbelt", "seat belt", "immobili", "child", "stability", "traction", "collision", "lane", "blind", "speed alert", "crash")),
    Cat("Comfort & convenience", Icons.Outlined.AcUnit, Electric, listOf("ac", "air con", "climate", "seat", "sunroof", "cruise", "keyless", "push",
        "power window", "steering", "armrest", "charger", "wireless charg", "ventilat", "mirror", "boot", "tailgate", "wiper", "rain", "auto")),
    Cat("Infotainment", Icons.Outlined.Tv, Amber, listOf("screen", "touch", "display", "carplay", "android", "speaker", "audio", "music", "bluetooth",
        "usb", "connected", "app", "navigation", "voice", "infotainment", "sound", "hud", "cluster")),
    Cat("Exterior & lighting", Icons.Outlined.Lightbulb, Ignition, listOf("led", "lamp", "light", "drl", "alloy", "wheel", "tyre", "roof", "spoiler",
        "grille", "chrome", "body colour", "paint", "fog")),
)
private val OTHER = Cat("Other", Icons.Outlined.MoreHoriz, Mute, emptyList())

private fun catOf(f: Feature): Cat {
    val t = (f.key + " " + f.label).lowercase()
    return CATS.firstOrNull { c -> c.words.any { w -> if (w.length <= 3) Regex("\\b$w\\b").containsMatchIn(t) else w in t } } ?: OTHER
}


/** Headline specs, matched by the API's normalised key or by the manufacturer's own label (brands word them differently). */
val HEADLINE_SPECS: List<Pair<String, Regex>> = listOf(
    "Engine" to Regex("displacement|engine capacity|cubic capacity|engine \\(cc\\)|^capacity", RegexOption.IGNORE_CASE),
    "Power" to Regex("max(imum)?[ _]?power|^power|peak power|motor power", RegexOption.IGNORE_CASE),
    "Torque" to Regex("torque", RegexOption.IGNORE_CASE),
    "Mileage" to Regex("mileage|fuel efficiency|fuel economy|arai", RegexOption.IGNORE_CASE),
    "Range" to Regex("range|driving range", RegexOption.IGNORE_CASE),
    "Battery" to Regex("battery (pack|capacity)|battery_capacity", RegexOption.IGNORE_CASE),
    "Seats" to Regex("seating", RegexOption.IGNORE_CASE),
    "Boot space" to Regex("boot|luggage|cargo", RegexOption.IGNORE_CASE),
    "Ground clearance" to Regex("ground clearance", RegexOption.IGNORE_CASE),
    "Kerb weight" to Regex("kerb weight|curb weight", RegexOption.IGNORE_CASE),
    "Fuel tank" to Regex("fuel tank", RegexOption.IGNORE_CASE),
)

fun findSpec(specs: List<com.onroad.app.data.Spec>?, rx: Regex): String? =
    specs?.firstOrNull { rx.containsMatchIn(it.key.replace('_', ' ')) || rx.containsMatchIn(it.label) }?.value

/**
 * Specs & features for the selected variant. Features are checked against the full list from the model's top variant,
 * so the buyer sees both what this variant has (✓) and what only costlier variants add (✗).
 */
@Composable
fun SpecsSection(brand: String, variantName: String, sp: VariantSpecs?, top: VariantSpecs?, img: (String?) -> String?) {
    var view by remember { mutableStateOf("features") }
    var filter by remember { mutableStateOf("all") }
    if (sp == null || (sp.specs.isEmpty() && sp.features.isEmpty())) {
        Text("$brand's spec sheet for this variant isn't published in a form we can read yet.", color = Mute, modifier = Modifier.padding(20.dp))
        return
    }
    val have = sp.features.map { it.label.lowercase() }.toSet()
    val missing = top?.features.orEmpty().filter { it.label.lowercase() !in have }
    val all = sp.features.map { it to true } + missing.map { it to false }
    Column(Modifier.padding(horizontal = 16.dp)) {
        // headline specs
        val keyVals = HEADLINE_SPECS.mapNotNull { (label, rx) -> findSpec(sp.specs, rx)?.let { label to it } }.take(6)
        if (keyVals.isNotEmpty()) {
            LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp), contentPadding = PaddingValues(bottom = 14.dp)) {
                items(keyVals, key = { it.first }) { (l, v) ->
                    Column(Modifier.clip(RoundedCornerShape(16.dp)).background(Panel).border(1.dp, Line, RoundedCornerShape(16.dp))
                        .padding(horizontal = 14.dp, vertical = 12.dp).width(120.dp)) {
                        Text(l.uppercase(), style = MaterialTheme.typography.labelSmall, color = Mute)
                        Spacer(Modifier.height(4.dp))
                        Text(v, style = MaterialTheme.typography.titleMedium, maxLines = 2, overflow = TextOverflow.Ellipsis)
                    }
                }
            }
        }
        // view switch
        Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(50)).background(Panel2).padding(4.dp)) {
            listOf("features" to "Features (${sp.features.size})", "specs" to "Specifications").forEach { (k, l) ->
                Text(l, fontWeight = FontWeight.SemiBold, color = if (view == k) Color.White else Mute,
                    textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                    modifier = Modifier.weight(1f).clip(RoundedCornerShape(50)).background(if (view == k) Ignition else Color.Transparent)
                        .clickable { view = k }.padding(vertical = 10.dp))
            }
        }
        Spacer(Modifier.height(14.dp))
        if (view == "features") {
            if (sp.features.isEmpty()) Text("No equipment list published for this variant.", color = Mute)
            else {
                // summary
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text(variantName, style = MaterialTheme.typography.titleMedium, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        Text(if (missing.isEmpty()) "${sp.features.size} features · fully loaded"
                             else "${sp.features.size} of ${all.size} features · ${missing.size} only in higher variants", color = Mute,
                            style = MaterialTheme.typography.bodySmall)
                    }
                }
                Spacer(Modifier.height(10.dp))
                if (missing.isNotEmpty()) Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf("all" to "All", "yes" to "Included", "no" to "Not in this variant").forEach { (k, l) ->
                        Text(l, style = MaterialTheme.typography.labelMedium, color = if (filter == k) Ink else Mute,
                            modifier = Modifier.clip(RoundedCornerShape(50)).border(1.dp, if (filter == k) Ink else Line, RoundedCornerShape(50))
                                .clickable { filter = k }.padding(horizontal = 12.dp, vertical = 7.dp))
                    }
                }
                // feature photos from the manufacturer, for what this variant has
                val photos = sp.features.filter { sp.photos.containsKey(it.key) }
                if (photos.isNotEmpty() && filter != "no") {
                    Spacer(Modifier.height(12.dp))
                    LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        items(photos, key = { "ph" + it.key }) { f ->
                            Column(Modifier.width(220.dp).clip(RoundedCornerShape(18.dp)).background(Panel).border(1.dp, Line, RoundedCornerShape(18.dp))) {
                                AsyncImage(img(sp.photos[f.key]?.imageUrl), f.label, contentScale = ContentScale.Crop, modifier = Modifier.fillMaxWidth().height(130.dp))
                                Text(f.label, style = MaterialTheme.typography.labelLarge, maxLines = 2, modifier = Modifier.padding(10.dp))
                            }
                        }
                    }
                }
                val shown = all.filter { (_, has) -> filter == "all" || (filter == "yes" && has) || (filter == "no" && !has) }
                (CATS + OTHER).forEach { c ->
                    val rows = shown.filter { catOf(it.first) == c }.sortedBy { !it.second }
                    if (rows.isNotEmpty()) FeatureGroup(c, rows)
                }
            }
        } else {
            sp.specs.groupBy { it.grp.ifBlank { "General" } }.forEach { (g, rows) -> SpecGroup(g, rows.map { it.label to it.value }) }
            if (sp.specs.isEmpty()) Text("No specifications published for this variant.", color = Mute)
        }
        Spacer(Modifier.height(8.dp))
        Text("From $brand's official spec sheet for this variant.", color = Mute, style = MaterialTheme.typography.bodySmall)
    }
}

@Composable
private fun FeatureGroup(c: Cat, rows: List<Pair<Feature, Boolean>>) {
    var open by remember(c.name) { mutableStateOf(true) }
    Column(Modifier.fillMaxWidth().padding(top = 12.dp).clip(RoundedCornerShape(20.dp)).background(Panel).border(1.dp, Line, RoundedCornerShape(20.dp))
        .animateContentSize()) {
        Row(Modifier.fillMaxWidth().clickable { open = !open }.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(36.dp).clip(RoundedCornerShape(11.dp)).background(c.tint.copy(alpha = 0.14f)), contentAlignment = Alignment.Center) {
                Icon(c.icon, null, tint = c.tint, modifier = Modifier.size(19.dp))
            }
            Spacer(Modifier.width(12.dp))
            Text(c.name, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
            Text("${rows.count { it.second }}/${rows.size}", color = Mute, style = MaterialTheme.typography.labelLarge)
            Icon(if (open) Icons.Outlined.KeyboardArrowUp else Icons.Outlined.KeyboardArrowDown, null, tint = Mute)
        }
        if (open) rows.forEachIndexed { i, (f, has) ->
            if (i > 0) HorizontalDivider(color = Line, modifier = Modifier.padding(start = 56.dp))
            Row(Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 11.dp), verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.size(24.dp).clip(CircleShape).background(if (has) Good.copy(alpha = 0.16f) else Panel2), contentAlignment = Alignment.Center) {
                    Icon(if (has) Icons.Outlined.Check else Icons.Outlined.Close, if (has) "Included" else "Not in this variant",
                        tint = if (has) Good else Mute, modifier = Modifier.size(15.dp))
                }
                Spacer(Modifier.width(18.dp))
                Text(f.label, color = if (has) Ink else Mute, textDecoration = if (has) null else TextDecoration.LineThrough,
                    style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
            }
        }
    }
}

@Composable
private fun SpecGroup(title: String, rows: List<Pair<String, String>>) {
    var open by remember(title) { mutableStateOf(true) }
    Column(Modifier.fillMaxWidth().padding(top = 12.dp).clip(RoundedCornerShape(20.dp)).background(Panel).border(1.dp, Line, RoundedCornerShape(20.dp))
        .animateContentSize()) {
        Row(Modifier.fillMaxWidth().clickable { open = !open }.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(36.dp).clip(RoundedCornerShape(11.dp)).background(Electric.copy(alpha = 0.14f)), contentAlignment = Alignment.Center) {
                Icon(Icons.Outlined.DirectionsCar, null, tint = Electric, modifier = Modifier.size(19.dp))
            }
            Spacer(Modifier.width(12.dp))
            Text(title, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
            Icon(if (open) Icons.Outlined.KeyboardArrowUp else Icons.Outlined.KeyboardArrowDown, null, tint = Mute)
        }
        if (open) rows.forEachIndexed { i, (l, v) ->
            if (i > 0) HorizontalDivider(color = Line, modifier = Modifier.padding(horizontal = 14.dp))
            Row(Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 11.dp)) {
                Text(l, color = Mute, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f).padding(end = 12.dp))
                Text(v, fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f),
                    textAlign = androidx.compose.ui.text.style.TextAlign.End)
            }
        }
    }
}
