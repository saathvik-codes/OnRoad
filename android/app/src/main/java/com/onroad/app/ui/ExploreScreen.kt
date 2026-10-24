package com.onroad.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
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

// Body types and fuels exactly as the API stores and filters them
private val CAR_BODIES = listOf("SUV", "Hatchback", "Sedan", "MUV", "Coupe", "Convertible", "Pickup")
private val BIKE_BODIES = listOf("Commuter", "Scooter", "Street", "Sports", "Adventure", "Cruiser", "Electric Scooter")
private val CAR_FUELS = listOf("Petrol", "Diesel", "CNG", "Hybrid", "Electric")
private val BIKE_FUELS = listOf("Petrol", "Electric")
private data class Budget(val id: String, val label: String, val hint: String, val min: Long?, val max: Long?)
private val BIKE_BUDGETS = listOf(
    Budget("b1", "Under ₹1 lakh", "Commuters, scooters", null, 100_000),
    Budget("b2", "₹1–2 lakh", "Most popular", 100_000, 200_000),
    Budget("b3", "₹2–5 lakh", "Premium", 200_000, 500_000),
    Budget("b4", "Above ₹5 lakh", "Superbikes", 500_000, null),
)
private val SORTS = listOf("popular" to "Most bought", "price" to "Price: low to high", "offers" to "With offers")

/** Browse every listed model: cars or bikes, filtered by budget, brand, body type and fuel. */
@Composable
fun ExploreScreen(onModel: (String) -> Unit, onSearch: () -> Unit, initType: String = "car", initBudget: String? = null,
                  vm: BrowseVM = hiltViewModel()) {
    val city by vm.prefs.city.collectAsStateWithLifecycle()
    var type by remember { mutableStateOf(initType) }
    var budget by remember { mutableStateOf(initBudget) }
    var brand by remember { mutableStateOf<String?>(null) }
    var body by remember { mutableStateOf<String?>(null) }
    var fuel by remember { mutableStateOf<String?>(null) }
    var sort by remember { mutableStateOf("popular") }
    var bands by remember { mutableStateOf<List<Band>>(emptyList()) }
    var brands by remember { mutableStateOf<List<Brand>>(emptyList()) }
    var list by remember { mutableStateOf<List<ModelSummary>?>(null) }
    var failed by remember { mutableStateOf(false) }
    var tick by remember { mutableIntStateOf(0) }
    val bike = type == "bike"
    val budgets = if (bike) BIKE_BUDGETS else bands.map { Budget(it.id, it.label, it.hint, null, null) }

    LaunchedEffect(type, city) {
        brands = runCatching { vm.api.brands(city, type) }.getOrElse { emptyList() }.filter { it.models > 0 }.sortedByDescending { it.models }
        if (bands.isEmpty()) bands = runCatching { vm.api.bands() }.getOrElse { emptyList() }
    }
    LaunchedEffect(city, type, budget, brand, body, fuel, sort, tick) {
        list = null; failed = false
        val bb = BIKE_BUDGETS.firstOrNull { it.id == budget }
        runCatching {
            vm.api.explore(city, brand = brand, band = if (bike) null else budget, sort = sort, type = type, body = body, fuel = fuel,
                minInr = bb?.min, maxInr = bb?.max)
        }.onSuccess { list = it }.onFailure { failed = true }
    }
    val active = listOfNotNull(budget, brand, body, fuel).size

    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 24.dp)) {
        item {
            Column(Modifier.padding(start = 16.dp, end = 16.dp, top = 12.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text("Explore", style = MaterialTheme.typography.headlineMedium)
                        Text("Official prices for $city", color = Mute, style = MaterialTheme.typography.bodyMedium)
                    }
                    IconButton(onSearch, Modifier.clip(CircleShape).background(Panel2)) { Icon(Icons.Outlined.Search, "Search") }
                }
                Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(50)).background(Panel2).padding(4.dp)) {
                    listOf("car" to "Cars", "bike" to "Bikes & scooters").forEach { (k, l) ->
                        Text(l, fontWeight = FontWeight.SemiBold, color = if (type == k) Color.White else Mute, textAlign = TextAlign.Center,
                            modifier = Modifier.weight(1f).clip(RoundedCornerShape(50)).background(if (type == k) Ignition else Color.Transparent)
                                .clickable { if (type != k) { type = k; budget = null; brand = null; body = null; fuel = null } }.padding(vertical = 10.dp))
                    }
                }
            }
            if (budgets.isNotEmpty()) {
                FilterLabel("Budget")
                LazyRow(contentPadding = PaddingValues(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    items(budgets, key = { it.id }) { b -> BudgetChip(b.label, b.hint, budget == b.id) { budget = if (budget == b.id) null else b.id } }
                }
            }
            if (brands.isNotEmpty()) {
                FilterLabel("Brand")
                LazyRow(contentPadding = PaddingValues(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    items(brands, key = { it.slug }) { b ->
                        val on = brand == b.slug
                        Column(Modifier.width(76.dp).clickable { brand = if (on) null else b.slug }, horizontalAlignment = Alignment.CenterHorizontally) {
                            Box(Modifier.size(64.dp).clip(RoundedCornerShape(18.dp)).background(Color.White)
                                .border(2.dp, if (on) Ignition else Color.Transparent, RoundedCornerShape(18.dp)).padding(10.dp),
                                contentAlignment = Alignment.Center) {
                                val logo = vm.prefs.img(b.logo, 200)
                                if (logo != null) AsyncImage(logo, b.name, contentScale = ContentScale.Fit, modifier = Modifier.fillMaxSize())
                                else Text(b.name.take(2), color = Color.Black, fontWeight = FontWeight.Bold)
                            }
                            Text(b.name, style = MaterialTheme.typography.labelMedium, color = if (on) Ignition else Mute, maxLines = 1,
                                overflow = TextOverflow.Ellipsis, modifier = Modifier.padding(top = 4.dp))
                        }
                    }
                }
            }
            FilterLabel("Body type")
            ChipRow(if (bike) BIKE_BODIES else CAR_BODIES, body) { body = it }
            FilterLabel("Fuel")
            ChipRow(if (bike) BIKE_FUELS else CAR_FUELS, fuel) { fuel = it }
            Row(Modifier.fillMaxWidth().padding(start = 16.dp, end = 8.dp, top = 18.dp), verticalAlignment = Alignment.CenterVertically) {
                Text(list?.let { "${it.size} ${if (bike) "bikes & scooters" else "cars"}" } ?: "Loading…",
                    style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                if (active > 0) TextButton({ budget = null; brand = null; body = null; fuel = null }) { Text("Clear ($active)", color = Ignition) }
            }
            LazyRow(contentPadding = PaddingValues(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                items(SORTS, key = { it.first }) { (k, l) ->
                    Text(l, style = MaterialTheme.typography.labelMedium, color = if (sort == k) Ink else Mute,
                        modifier = Modifier.clip(RoundedCornerShape(50)).border(1.dp, if (sort == k) Ink else Line, RoundedCornerShape(50))
                            .clickable { sort = k }.padding(horizontal = 12.dp, vertical = 7.dp))
                }
            }
            Spacer(Modifier.height(8.dp))
        }
        val l = list
        when {
            failed -> item { ErrorState("Couldn't reach OnRoad. Check your connection.") { tick++ } }
            l == null -> item { Box(Modifier.fillMaxWidth().padding(40.dp), contentAlignment = Alignment.Center) { CircularProgressIndicator(color = Ignition) } }
            l.isEmpty() -> item { Text("Nothing matches these filters in $city. Try removing one.", color = Mute, modifier = Modifier.padding(20.dp)) }
            else -> items(l, key = { it.id }) { m -> ModelCard(m, vm.prefs.img(m.imageUrl, 480)) { onModel(m.id) } }
        }
    }
}

@Composable
private fun FilterLabel(t: String) = Text(t.uppercase(), style = MaterialTheme.typography.labelSmall, color = Mute,
    modifier = Modifier.padding(start = 16.dp, top = 18.dp, bottom = 8.dp))

@Composable
private fun BudgetChip(label: String, hint: String?, on: Boolean, onClick: () -> Unit) = Column(
    Modifier.clip(RoundedCornerShape(16.dp)).background(if (on) Ignition.copy(alpha = 0.15f) else Panel)
        .border(1.dp, if (on) Ignition else Line, RoundedCornerShape(16.dp)).clickable(onClick = onClick).padding(horizontal = 14.dp, vertical = 10.dp),
) {
    Text(label, fontWeight = FontWeight.SemiBold, color = if (on) Ignition else Ink)
    hint?.let { Text(it, color = Mute, style = MaterialTheme.typography.bodySmall) }
}

@Composable
private fun ChipRow(options: List<String>, sel: String?, onSel: (String?) -> Unit) =
    LazyRow(contentPadding = PaddingValues(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        items(options, key = { it }) { o ->
            val on = sel == o
            Text(o, style = MaterialTheme.typography.labelLarge, color = if (on) Color.White else Ink,
                modifier = Modifier.clip(RoundedCornerShape(50)).background(if (on) Ignition else Panel2)
                    .clickable { onSel(if (on) null else o) }.padding(horizontal = 16.dp, vertical = 9.dp))
        }
    }
