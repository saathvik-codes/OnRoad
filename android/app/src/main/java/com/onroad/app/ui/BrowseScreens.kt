package com.onroad.app.ui

import androidx.compose.foundation.clickable
import androidx.compose.ui.draw.clip
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.MyLocation
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil3.compose.AsyncImage
import com.onroad.app.data.Api
import com.onroad.app.data.City
import com.onroad.app.data.Hit
import com.onroad.app.data.ModelSummary
import com.onroad.app.data.Prefs
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.delay
import javax.inject.Inject

@HiltViewModel
class BrowseVM @Inject constructor(val api: Api, val prefs: Prefs) : ViewModel()

@Composable
private fun Header(title: String, sub: String? = null, onBack: () -> Unit) = Row(
    Modifier.fillMaxWidth().statusBarsPadding().padding(start = 4.dp, end = 16.dp, top = 6.dp), verticalAlignment = Alignment.CenterVertically,
) {
    IconButton(onBack) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "Back") }
    Column { Text(title, style = MaterialTheme.typography.titleLarge); sub?.let { Text(it, color = Mute, style = MaterialTheme.typography.bodyMedium) } }
}

/** One brand's line-up, grouped by body type (Hatchback, Sedan, SUV…), most-bought first. */
@Composable
fun BrandScreen(slug: String, name: String, onModel: (String) -> Unit, onBack: () -> Unit, vm: BrowseVM = hiltViewModel()) {
    val city by vm.prefs.city.collectAsStateWithLifecycle()
    var models by remember { mutableStateOf<List<ModelSummary>?>(null) }
    LaunchedEffect(slug, city) { models = runCatching { vm.api.explore(city, brand = slug) }.getOrDefault(emptyList()) }
    val order = listOf("Hatchback", "Sedan", "SUV", "MUV", "Pickup", "Coupe", "Convertible")
    val groups = models.orEmpty().groupBy { it.bodyType ?: "Other" }.toList()
        .sortedBy { order.indexOf(it.first).let { i -> if (i < 0) 99 else i } }
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 24.dp)) {
        item { Header(name, models?.let { "${it.size} models · prices for $city" }, onBack) }
        if (models?.isEmpty() == true) item { Text("No prices published by $name right now.", color = Mute, modifier = Modifier.padding(20.dp)) }
        groups.forEach { (type, list) ->
            item { Text("${type}s".replace("Others", "Other"), style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(start = 16.dp, top = 18.dp, bottom = 8.dp)) }
            items(list, key = { it.id }) { m -> ModelCard(m, vm.prefs.img(m.imageUrl, 800)) { onModel(m.id) } }
        }
    }
}

@Composable
fun ModelCard(m: ModelSummary, img: String?, onClick: () -> Unit) = Tile(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 6.dp).clickable(onClick = onClick), pad = 14) {
    Column {
        AsyncImage(img, m.name, contentScale = ContentScale.Fit, modifier = Modifier.fillMaxWidth().aspectRatio(16 / 9f))
        Spacer(Modifier.height(8.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(m.name, style = MaterialTheme.typography.titleLarge, modifier = Modifier.weight(1f))
            m.salesRank?.takeIf { it <= 25 }?.let { Chip("#$it in India", Ignition) }
        }
        Text(range(m.fromInr, m.toInr), style = MaterialTheme.typography.titleMedium, color = Ink)
        Spacer(Modifier.height(6.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            if (m.variants > 0) Chip("${m.variants} variants")
            m.fuels?.split(",")?.filter { it.isNotBlank() }?.forEach { Chip(it) }
            if (m.offers > 0) Chip("${m.offers} offer${if (m.offers > 1) "s" else ""}", Good)
        }
    }
}

@Composable
fun SearchScreen(onModel: (String) -> Unit, onBack: () -> Unit, vm: BrowseVM = hiltViewModel()) {
    var q by remember { mutableStateOf("") }
    var hits by remember { mutableStateOf<List<Hit>>(emptyList()) }
    LaunchedEffect(q) { delay(200); hits = if (q.trim().length >= 2) runCatching { vm.api.search(q.trim()) }.getOrDefault(emptyList()) else emptyList() }
    LazyColumn(Modifier.fillMaxSize()) {
        item {
            Header("Search", null, onBack)
            OutlinedTextField(q, { q = it }, placeholder = { Text("Creta, Nexon, Thar…") }, singleLine = true, shape = RoundedCornerShape(16.dp),
                modifier = Modifier.fillMaxWidth().padding(16.dp))
        }
        items(hits, key = { it.id }) { h ->
            Row(Modifier.fillMaxWidth().clickable { onModel(h.id) }.padding(horizontal = 20.dp, vertical = 14.dp)) {
                Text("${h.brand} ${h.name}", modifier = Modifier.weight(1f), style = MaterialTheme.typography.titleMedium)
                Text(lakh(h.fromInr), color = Mute)
            }
        }
    }
}

/** City list (prices + road tax follow the city). "Use my location" takes a fresh fix and picks the nearest supported city. */
@Composable
fun CityScreen(onBack: () -> Unit, vm: BrowseVM = hiltViewModel()) {
    var cities by remember { mutableStateOf<List<City>>(emptyList()) }
    var q by remember { mutableStateOf("") }
    var status by remember { mutableStateOf<String?>(null) }
    val city by vm.prefs.city.collectAsStateWithLifecycle()
    LaunchedEffect(Unit) { cities = runCatching { vm.api.cities() }.getOrDefault(emptyList()) }
    val locate = com.onroad.app.data.rememberLocator(vm.prefs) { loc ->
        if (loc == null) { status = "Couldn't get your location. Turn on location, or pick your city below."; return@rememberLocator }
        val near = cities.minByOrNull { com.onroad.app.data.kmBetween(loc.latitude, loc.longitude, it.lat, it.lng) }
        if (near == null) { status = "City list didn't load. Check your connection."; return@rememberLocator }
        val km = com.onroad.app.data.kmBetween(loc.latitude, loc.longitude, near.lat, near.lng)
        vm.prefs.setCity(near.name)
        status = "Prices for ${near.name}, ${near.stateName} (${"%.0f".format(km)} km from you). Showrooms are sorted by distance from where you are."
    }
    LazyColumn(Modifier.fillMaxSize()) {
        item {
            Header("Your city", "Prices and road tax follow your city", onBack)
            Row(Modifier.fillMaxWidth().padding(16.dp).clip(RoundedCornerShape(16.dp)).background(Ignition.copy(alpha = 0.12f))
                .clickable { status = "Finding you…"; locate() }.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Outlined.MyLocation, null, tint = Ignition); Spacer(Modifier.padding(6.dp))
                Column {
                    Text("Use my location", color = Ignition, style = MaterialTheme.typography.titleMedium)
                    Text(status ?: "Nearest city for prices, nearest showrooms by distance", color = Mute, style = MaterialTheme.typography.bodySmall)
                }
            }
            OutlinedTextField(q, { q = it }, placeholder = { Text("Search city or state") }, singleLine = true, shape = RoundedCornerShape(16.dp),
                modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp))
        }
        items(cities.filter { "${it.name} ${it.stateName}".contains(q, true) }, key = { it.name }) { c ->
            Row(Modifier.fillMaxWidth().clickable { vm.prefs.setCity(c.name); onBack() }.padding(horizontal = 20.dp, vertical = 14.dp)) {
                Column(Modifier.weight(1f)) { Text(c.name, style = MaterialTheme.typography.titleMedium); Text(c.stateName, color = Mute) }
                if (c.name == city) Chip("Selected", Ignition)
            }
        }
    }
}
