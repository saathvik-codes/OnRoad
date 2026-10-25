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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.automirrored.outlined.Sort
import androidx.compose.material.icons.outlined.Check
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material.icons.outlined.ElectricCar
import androidx.compose.material.icons.outlined.LocalGasStation
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material.icons.outlined.Tune
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
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
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil3.compose.AsyncImage
import com.onroad.app.data.Band
import com.onroad.app.data.Brand
import com.onroad.app.data.ModelSummary

// Filter values exactly as the API stores them
internal val CAR_BODIES = listOf("SUV", "Hatchback", "Sedan", "MUV", "Coupe", "Convertible", "Pickup")
internal val BIKE_BODIES = listOf("Commuter", "Scooter", "Street", "Sports", "Adventure", "Cruiser", "Electric Scooter")
internal val CAR_FUELS = listOf("Petrol", "Diesel", "CNG", "Hybrid", "Electric")
internal val BIKE_FUELS = listOf("Petrol", "Electric")
internal val GEARBOX = listOf("Manual", "Automatic")
private data class Budget(val id: String, val label: String, val hint: String, val min: Long?, val max: Long?)
private val BIKE_BUDGETS = listOf(
    Budget("b1", "Under ₹1 lakh", "Commuters, scooters", null, 100_000), Budget("b2", "₹1–2 lakh", "Most popular", 100_000, 200_000),
    Budget("b3", "₹2–5 lakh", "Premium", 200_000, 500_000), Budget("b4", "Above ₹5 lakh", "Superbikes", 500_000, null),
)
private val SORTS = listOf("popular" to "Most bought", "price" to "Price: low to high", "price_desc" to "Price: high to low", "offers" to "With offers")

/** Every active filter. Multi-select within a group, AND across groups (like any shopping app). */
private data class Filters(val budget: String? = null, val brands: Set<String> = emptySet(), val bodies: Set<String> = emptySet(),
                           val fuels: Set<String> = emptySet(), val gearbox: Set<String> = emptySet()) {
    val count get() = (if (budget != null) 1 else 0) + brands.size + bodies.size + fuels.size + gearbox.size
}

private fun isAuto(t: String) = t.isNotBlank() && !t.equals("manual", true)

private fun matches(m: ModelSummary, f: Filters, budgets: List<Budget>, skip: String? = null): Boolean {
    if (skip != "budget" && f.budget != null) {
        val b = budgets.firstOrNull { it.id == f.budget }
        val p = m.fromInr ?: return false
        if (b != null && ((b.min != null && p < b.min) || (b.max != null && p >= b.max))) return false
    }
    if (skip != "brand" && f.brands.isNotEmpty() && m.brandSlug !in f.brands) return false
    if (skip != "body" && f.bodies.isNotEmpty() && (m.bodyType ?: "") !in f.bodies) return false
    val fuels = (m.fuels ?: "").split(",").map { it.trim().lowercase() }
    if (skip != "fuel" && f.fuels.isNotEmpty() && f.fuels.none { want -> fuels.any { it.contains(want.lowercase()) } }) return false
    val tr = (m.transmissions ?: "").split(",").map { it.trim() }.filter { it.isNotBlank() }
    if (skip != "gearbox" && f.gearbox.isNotEmpty()) {
        val ok = ("Manual" in f.gearbox && tr.any { !isAuto(it) }) || ("Automatic" in f.gearbox && tr.any { isAuto(it) })
        if (!ok) return false
    }
    return true
}

/** Browse every listed model, Myntra-style: sort + filters pinned above the tab bar, filters in a two-pane sheet. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ExploreScreen(onModel: (String) -> Unit, onSearch: () -> Unit, initType: String = "car", initBudget: String? = null,
                  brand: Pair<String, String>? = null, onBack: (() -> Unit)? = null, vm: BrowseVM = hiltViewModel()) {
    val city by vm.prefs.city.collectAsStateWithLifecycle()
    var type by remember { mutableStateOf(initType) }
    var f by remember { mutableStateOf(Filters(budget = initBudget)) }
    var sort by remember { mutableStateOf("popular") }
    var bands by remember { mutableStateOf<List<Band>>(emptyList()) }
    var brands by remember { mutableStateOf<List<Brand>>(emptyList()) }
    var all by remember { mutableStateOf<List<ModelSummary>?>(null) }
    var failed by remember { mutableStateOf(false) }
    var tick by remember { mutableIntStateOf(0) }
    var sheet by remember { mutableStateOf<String?>(null) }      // "sort" | "filters"
    val bike = type == "bike"
    val budgets = if (bike) BIKE_BUDGETS else bands.map { Budget(it.id, it.label, it.hint, it.min, it.max) }

    // one brand's page: is it a car or a two-wheeler maker?
    LaunchedEffect(brand?.first) {
        val slug = brand?.first ?: return@LaunchedEffect
        val bikeMaker = runCatching { vm.api.brands(city, "bike") }.getOrElse { emptyList() }.any { it.slug == slug }
        type = if (bikeMaker) "bike" else "car"
    }
    LaunchedEffect(type, city) {
        brands = runCatching { vm.api.brands(city, type) }.getOrElse { emptyList() }.filter { it.models > 0 }.sortedByDescending { it.models }
        if (bands.isEmpty()) bands = runCatching { vm.api.bands() }.getOrElse { emptyList() }
    }
    LaunchedEffect(city, type, tick) {
        all = null; failed = false
        runCatching { vm.api.explore(city, type = type) }.onSuccess { all = it }.onFailure { failed = true }
    }
    val scoped = all?.filter { m -> brand == null || m.brandSlug == brand.first }
    val shown = scoped?.filter { matches(it, f, budgets) }?.let { l ->
        when (sort) {
            "price" -> l.sortedBy { it.fromInr ?: Long.MAX_VALUE }
            "price_desc" -> l.sortedByDescending { it.fromInr ?: 0 }
            "offers" -> l.sortedByDescending { it.offers }
            else -> l                                                            // API order = most bought first
        }
    }

    Box(Modifier.fillMaxSize()) {
        LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 90.dp)) {
            item {
                Column(Modifier.padding(start = 16.dp, end = 16.dp, top = 12.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        if (onBack != null) IconButton(onBack) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "Back") }
                        Column(Modifier.weight(1f)) {
                            Text(brand?.second ?: "Explore", style = MaterialTheme.typography.headlineMedium)
                            Text(if (brand != null) "${scoped?.size ?: "…"} models · official prices for $city" else "Official prices for $city",
                                color = Mute, style = MaterialTheme.typography.bodyMedium)
                        }
                        if (brand == null) IconButton(onSearch, Modifier.clip(CircleShape).background(Panel2)) { Icon(Icons.Outlined.Search, "Search") }
                    }
                    if (brand == null) Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(50)).background(Panel2).padding(4.dp)) {
                        listOf("car" to "Cars", "bike" to "Bikes & scooters").forEach { (k, l) ->
                            Text(l, fontWeight = FontWeight.SemiBold, color = if (type == k) Color.White else Mute, textAlign = TextAlign.Center,
                                modifier = Modifier.weight(1f).clip(RoundedCornerShape(50)).background(if (type == k) Ignition else Color.Transparent)
                                    .clickable { if (type != k) { type = k; f = Filters() } }.padding(vertical = 10.dp))
                        }
                    }
                }
                // brand strip: quick multi-select
                if (brands.isNotEmpty() && brand == null) LazyRow(contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 16.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    items(brands, key = { it.slug }) { b -> BrandLogo(b, b.slug in f.brands, vm.prefs.img(b.logo, 200)) { f = f.copy(brands = f.brands.toggle(b.slug)) } }
                }
                // active filters as removable chips
                val active = buildList {
                    f.budget?.let { id -> budgets.firstOrNull { it.id == id }?.let { add(it.label to { f = f.copy(budget = null) }) } }
                    f.brands.forEach { s -> add((brands.firstOrNull { it.slug == s }?.name ?: s) to { f = f.copy(brands = f.brands - s) }) }
                    f.bodies.forEach { b -> add(b to { f = f.copy(bodies = f.bodies - b) }) }
                    f.fuels.forEach { x -> add(x to { f = f.copy(fuels = f.fuels - x) }) }
                    f.gearbox.forEach { g -> add(g to { f = f.copy(gearbox = f.gearbox - g) }) }
                }
                if (active.isNotEmpty()) LazyRow(contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 14.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(active.size) { i ->
                        val (label, remove) = active[i]
                        Row(Modifier.clip(RoundedCornerShape(50)).background(Ignition.copy(alpha = 0.14f)).border(1.dp, Ignition.copy(alpha = 0.5f), RoundedCornerShape(50))
                            .clickable { remove() }.padding(start = 12.dp, end = 8.dp, top = 7.dp, bottom = 7.dp), verticalAlignment = Alignment.CenterVertically) {
                            Text(label, style = MaterialTheme.typography.labelLarge, color = Ink); Spacer(Modifier.width(4.dp))
                            Icon(Icons.Outlined.Close, "Remove", tint = Ignition, modifier = Modifier.size(15.dp))
                        }
                    }
                    item { Text("Clear all", color = Ignition, style = MaterialTheme.typography.labelLarge,
                        modifier = Modifier.clickable { f = Filters() }.padding(horizontal = 6.dp, vertical = 7.dp)) }
                }
                Text(shown?.let { "${it.size} ${if (bike) "bikes & scooters" else "cars"}" } ?: "Loading…", style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.padding(start = 16.dp, top = 16.dp, bottom = 6.dp))
            }
            when {
                failed -> item { ErrorState("Couldn't reach OnRoad. Check your connection.") { tick++ } }
                shown == null -> item { Box(Modifier.fillMaxWidth().padding(40.dp), contentAlignment = Alignment.Center) { CircularProgressIndicator(color = Ignition) } }
                shown.isEmpty() -> item {
                    Column(Modifier.fillMaxWidth().padding(28.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                        Art("empty-search")
                        Text("Nothing matches all of these in $city.", color = Mute)
                        TextButton({ f = Filters() }) { Text("Clear filters", color = Ignition) }
                    }
                }
                else -> items(shown, key = { it.id }) { m -> ModelCard(m, vm.prefs.img(m.imageUrl, 480)) { onModel(m.id) } }
            }
        }
        // pinned action bar (Myntra-style), just above the bottom navigation
        Row(Modifier.align(Alignment.BottomCenter).fillMaxWidth()
            .background(Brush.verticalGradient(listOf(Color.Transparent, Night.copy(alpha = 0.95f), Night)))
            .then(if (onBack != null) Modifier.navigationBarsPadding() else Modifier)
            .padding(start = 14.dp, end = 14.dp, top = 16.dp, bottom = 10.dp)) {
            Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(50)).background(Panel2).border(1.dp, Line, RoundedCornerShape(50))) {
                BarButton(Icons.AutoMirrored.Outlined.Sort, "Sort", SORTS.first { it.first == sort }.second, Modifier.weight(1f)) { sheet = "sort" }
                Box(Modifier.width(1.dp).height(44.dp).background(Line).align(Alignment.CenterVertically))
                BarButton(Icons.Outlined.Tune, "Filters", if (f.count > 0) "${f.count} applied" else "None", Modifier.weight(1f), badge = f.count) { sheet = "filters" }
            }
        }
    }

    if (sheet == "sort") ModalBottomSheet({ sheet = null }, containerColor = Panel) {
        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 28.dp).navigationBarsPadding()) {
            Text("Sort by", style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(bottom = 8.dp))
            SORTS.forEach { (k, l) ->
                Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(14.dp)).clickable { sort = k; sheet = null }.padding(vertical = 14.dp, horizontal = 6.dp),
                    verticalAlignment = Alignment.CenterVertically) {
                    Text(l, Modifier.weight(1f), fontWeight = if (sort == k) FontWeight.SemiBold else FontWeight.Normal, color = if (sort == k) Ignition else Ink)
                    if (sort == k) Icon(Icons.Outlined.Check, null, tint = Ignition)
                }
            }
        }
    }
    if (sheet == "filters") {
        val state = rememberModalBottomSheetState(skipPartiallyExpanded = true)
        ModalBottomSheet({ sheet = null }, sheetState = state, containerColor = Panel) {
            FilterSheet(scoped.orEmpty(), f, budgets, if (brand != null) emptyList() else brands, bike, { vm.prefs.img(it, 200) },
                onChange = { f = it }, onDone = { sheet = null })
        }
    }
}

internal fun <T> Set<T>.toggle(x: T) = if (x in this) this - x else this + x

@Composable
internal fun BarButton(icon: androidx.compose.ui.graphics.vector.ImageVector, title: String, sub: String, modifier: Modifier, badge: Int = 0, onClick: () -> Unit) = Row(
    modifier.clip(RoundedCornerShape(50)).clickable(onClick = onClick).padding(vertical = 10.dp, horizontal = 16.dp),
    verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.Center,
) {
    Box {
        Icon(icon, null, tint = Ink, modifier = Modifier.size(22.dp))
        if (badge > 0) Box(Modifier.align(Alignment.TopEnd).size(9.dp).clip(CircleShape).background(Ignition))
    }
    Spacer(Modifier.width(10.dp))
    Column {
        Text(title.uppercase(), style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.Bold)
        Text(sub, style = MaterialTheme.typography.bodySmall, color = if (badge > 0) Ignition else Mute, maxLines = 1, overflow = TextOverflow.Ellipsis)
    }
}

@Composable
internal fun BrandLogo(b: Brand, on: Boolean, logo: String?, onClick: () -> Unit) = Column(
    Modifier.width(72.dp).clickable(onClick = onClick), horizontalAlignment = Alignment.CenterHorizontally,
) {
    Box(Modifier.size(60.dp).clip(RoundedCornerShape(18.dp)).background(Color.White)
        .border(2.dp, if (on) Ignition else Color.Transparent, RoundedCornerShape(18.dp)).padding(9.dp), contentAlignment = Alignment.Center) {
        if (logo != null) AsyncImage(logo, b.name, contentScale = ContentScale.Fit, modifier = Modifier.fillMaxSize())
        else Text(b.name.take(2), color = Color.Black, fontWeight = FontWeight.Bold)
        if (on) Box(Modifier.align(Alignment.TopEnd).size(16.dp).clip(CircleShape).background(Ignition), contentAlignment = Alignment.Center) {
            Icon(Icons.Outlined.Check, null, tint = Color.White, modifier = Modifier.size(11.dp))
        }
    }
    Text(b.name, style = MaterialTheme.typography.labelMedium, color = if (on) Ignition else Mute, maxLines = 1, overflow = TextOverflow.Ellipsis,
        modifier = Modifier.padding(top = 4.dp))
}

/** Two-pane filter sheet: categories on the left (dot when active), options with live counts on the right. */
@Composable
private fun FilterSheet(all: List<ModelSummary>, f0: Filters, budgets: List<Budget>, brands: List<Brand>, bike: Boolean,
                        logo: (String?) -> String?, onChange: (Filters) -> Unit, onDone: () -> Unit) {
    var f by remember { mutableStateOf(f0) }
    var cat by remember { mutableStateOf("Budget") }
    val cats = listOf("Budget") + (if (brands.isEmpty()) emptyList() else listOf("Brand")) + listOf("Body type", "Fuel") +
        if (bike) emptyList() else listOf("Gearbox")
    fun count(skip: String, test: (ModelSummary) -> Boolean) = all.count { matches(it, f, budgets, skip) && test(it) }
    val total = all.count { matches(it, f, budgets) }
    fun set(n: Filters) { f = n; onChange(n) }

    Column(Modifier.fillMaxWidth().fillMaxHeight(0.82f)) {
        Row(Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
            Text("Filters", style = MaterialTheme.typography.titleLarge, modifier = Modifier.weight(1f))
            if (f.count > 0) TextButton({ set(Filters()) }) { Text("Clear all", color = Ignition) }
        }
        Row(Modifier.weight(1f)) {
            // left rail
            Column(Modifier.width(118.dp).fillMaxHeight().background(Night)) {
                cats.forEach { c ->
                    val activeHere = when (c) { "Budget" -> f.budget != null; "Brand" -> f.brands.isNotEmpty(); "Body type" -> f.bodies.isNotEmpty()
                        "Fuel" -> f.fuels.isNotEmpty(); else -> f.gearbox.isNotEmpty() }
                    Row(Modifier.fillMaxWidth().background(if (cat == c) Panel else Color.Transparent).clickable { cat = c }.padding(start = 0.dp),
                        verticalAlignment = Alignment.CenterVertically) {
                        Box(Modifier.width(3.dp).height(48.dp).background(if (cat == c) Ignition else Color.Transparent))
                        Text(c, Modifier.weight(1f).padding(start = 13.dp), fontWeight = if (cat == c) FontWeight.SemiBold else FontWeight.Normal,
                            color = if (cat == c) Ink else Mute, style = MaterialTheme.typography.bodyMedium)
                        if (activeHere) Box(Modifier.padding(end = 10.dp).size(7.dp).clip(CircleShape).background(Ignition))
                    }
                }
            }
            // options
            AnimatedContent(cat, Modifier.weight(1f).fillMaxHeight(), label = "cat") { c ->
                Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    when (c) {
                        "Budget" -> budgets.forEach { b ->
                            val n = count("budget") { m -> m.fromInr != null && (b.min == null || m.fromInr >= b.min) && (b.max == null || m.fromInr < b.max) }
                            OptionCard(b.label, b.hint, n, f.budget == b.id, radio = true) { set(f.copy(budget = if (f.budget == b.id) null else b.id)) }
                        }
                        "Brand" -> FlowRow(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                            brands.forEach { b ->
                                val n = count("brand") { it.brandSlug == b.slug }
                                Column(Modifier.width(78.dp).clickable(enabled = n > 0 || b.slug in f.brands) { set(f.copy(brands = f.brands.toggle(b.slug))) },
                                    horizontalAlignment = Alignment.CenterHorizontally) {
                                    BrandLogo(b, b.slug in f.brands, logo(b.logo)) { set(f.copy(brands = f.brands.toggle(b.slug))) }
                                    Text("$n", style = MaterialTheme.typography.labelSmall, color = Mute)
                                }
                            }
                        }
                        "Body type" -> (if (bike) BIKE_BODIES else CAR_BODIES).forEach { b ->
                            OptionCard(b, null, count("body") { it.bodyType == b }, b in f.bodies) { set(f.copy(bodies = f.bodies.toggle(b))) }
                        }
                        "Fuel" -> (if (bike) BIKE_FUELS else CAR_FUELS).forEach { x ->
                            OptionCard(x, null, count("fuel") { m -> (m.fuels ?: "").lowercase().contains(x.lowercase()) }, x in f.fuels,
                                icon = if (x == "Electric") Icons.Outlined.ElectricCar else Icons.Outlined.LocalGasStation) { set(f.copy(fuels = f.fuels.toggle(x))) }
                        }
                        else -> GEARBOX.forEach { g ->
                            val n = count("gearbox") { m ->
                                val tr = (m.transmissions ?: "").split(",").map { it.trim() }.filter { it.isNotBlank() }
                                if (g == "Manual") tr.any { !isAuto(it) } else tr.any { isAuto(it) }
                            }
                            OptionCard(g, if (g == "Automatic") "AMT, CVT, DCT, torque converter, EV" else null, n, g in f.gearbox) { set(f.copy(gearbox = f.gearbox.toggle(g))) }
                        }
                    }
                }
            }
        }
        Row(Modifier.fillMaxWidth().background(Panel).padding(horizontal = 16.dp, vertical = 12.dp).navigationBarsPadding(),
            horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text("$total", style = MaterialTheme.typography.titleLarge)
                Text(if (bike) "bikes & scooters" else "cars", color = Mute, style = MaterialTheme.typography.bodySmall)
            }
            Button(onDone, Modifier.height(50.dp), enabled = total > 0, colors = ButtonDefaults.buttonColors(containerColor = Ignition)) {
                Text(if (total > 0) "Show results" else "No matches", fontWeight = FontWeight.SemiBold)
            }
        }
    }
}

@Composable
internal fun OptionCard(title: String, hint: String?, count: Int?, on: Boolean, radio: Boolean = false,
                       icon: androidx.compose.ui.graphics.vector.ImageVector? = null, onClick: () -> Unit) = Row(
    Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(if (on) Ignition.copy(alpha = 0.12f) else Panel2)
        .border(1.dp, if (on) Ignition else Color.Transparent, RoundedCornerShape(16.dp))
        .clickable(enabled = count == null || count > 0 || on, onClick = onClick).padding(horizontal = 14.dp, vertical = 12.dp),
    verticalAlignment = Alignment.CenterVertically,
) {
    Box(Modifier.size(22.dp).clip(if (radio) CircleShape else RoundedCornerShape(6.dp)).background(if (on) Ignition else Color.Transparent)
        .border(1.5.dp, if (on) Ignition else Mute, if (radio) CircleShape else RoundedCornerShape(6.dp)), contentAlignment = Alignment.Center) {
        if (on) Icon(Icons.Outlined.Check, null, tint = Color.White, modifier = Modifier.size(14.dp))
    }
    Spacer(Modifier.width(12.dp))
    icon?.let { Icon(it, null, tint = Mute, modifier = Modifier.size(18.dp)); Spacer(Modifier.width(8.dp)) }
    Column(Modifier.weight(1f)) {
        Text(title, fontWeight = FontWeight.SemiBold, color = if (count == 0 && !on) Mute.copy(alpha = 0.5f) else Ink)
        hint?.let { Text(it, color = Mute, style = MaterialTheme.typography.bodySmall) }
    }
    count?.let { Text("$it", color = Mute, style = MaterialTheme.typography.labelLarge) }
}
