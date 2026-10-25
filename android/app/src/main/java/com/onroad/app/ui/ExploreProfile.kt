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
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.KeyboardArrowRight
import androidx.compose.material.icons.automirrored.outlined.Logout
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.Bookmark
import androidx.compose.material.icons.outlined.Calculate
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material.icons.outlined.LocalOffer
import androidx.compose.material.icons.outlined.LocationOn
import androidx.compose.material.icons.automirrored.outlined.MenuBook
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.RequestQuote
import androidx.compose.material.icons.outlined.Storefront
import androidx.compose.material.icons.outlined.Palette
import androidx.compose.material.icons.outlined.Verified
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil3.compose.AsyncImage
import com.onroad.app.data.MyRequest
import com.onroad.app.data.SavedCar
import kotlinx.coroutines.launch

/** Profile: identity header, shortcut tiles, saved cars and dealer quotes, then grouped settings. */
@Composable
fun ProfileScreen(onSignIn: () -> Unit, onModel: (String) -> Unit, onCity: () -> Unit, onGuide: () -> Unit,
                  onShowrooms: () -> Unit = {}, onOffers: () -> Unit = {}, onFinder: () -> Unit = {}, onCalc: () -> Unit = {},
                  vm: BrowseVM = hiltViewModel()) {
    val acc by vm.prefs.account.collectAsStateWithLifecycle()
    val city by vm.prefs.city.collectAsStateWithLifecycle()
    val scope = rememberCoroutineScope()
    var saved by remember { mutableStateOf<List<SavedCar>>(emptyList()) }
    var quotes by remember { mutableStateOf<List<MyRequest>>(emptyList()) }
    var alerts by remember { mutableStateOf(vm.prefs.alerts) }
    LaunchedEffect(Unit) {
        if (vm.prefs.session != null) runCatching { vm.api.me() }.onSuccess { vm.prefs.setAccount(it) }.onFailure { vm.prefs.setAccount(null) }
    }
    LaunchedEffect(acc) {
        if (acc != null) {
            saved = runCatching { vm.api.saved() }.getOrElse { emptyList() }
            quotes = runCatching { vm.api.myQuotes() }.getOrElse { emptyList() }
        } else { saved = emptyList(); quotes = emptyList() }
    }
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 28.dp)) {
        item {
            Box(Modifier.fillMaxWidth().background(Brush.verticalGradient(if (IsDark) listOf(Color(0xFF4A1A12), Color(0xFF241020), Night) else listOf(Color(0xFFFFE1D8), Color(0xFFFFF1EC), Night)))
                .padding(start = 20.dp, end = 20.dp, top = 24.dp, bottom = 20.dp)) {
                Column {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(Modifier.size(68.dp).clip(CircleShape).background(IgnitionGradient).border(3.dp, Color.White.copy(alpha = 0.15f), CircleShape),
                            contentAlignment = Alignment.Center) {
                            val a = acc
                            if (a != null && a.name.isNotBlank()) Text(a.name.take(1).uppercase(), style = MaterialTheme.typography.headlineMedium, color = Color.White)
                            else Icon(Icons.Outlined.Person, null, tint = Color.White, modifier = Modifier.size(34.dp))
                        }
                        Spacer(Modifier.width(16.dp))
                        Column(Modifier.weight(1f)) {
                            Text(acc?.name?.ifBlank { null } ?: "Welcome to OnRoad", style = MaterialTheme.typography.headlineSmall)
                            Text(acc?.email ?: "Real on-road prices, nearest showrooms, dealer quotes", color = Mute, style = MaterialTheme.typography.bodyMedium)
                            if (acc != null) Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(top = 4.dp)) {
                                Icon(Icons.Outlined.LocationOn, null, tint = Ignition, modifier = Modifier.size(14.dp)); Spacer(Modifier.width(4.dp))
                                Text(city, style = MaterialTheme.typography.labelMedium)
                            }
                        }
                    }
                    Spacer(Modifier.height(18.dp))
                    if (acc == null) {
                        Button(onSignIn, Modifier.fillMaxWidth().height(52.dp), colors = ButtonDefaults.buttonColors(containerColor = Ignition)) {
                            Text("Sign in or create account", fontWeight = FontWeight.SemiBold)
                        }
                    } else {
                        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                            Stat("${saved.size}", "Saved", Modifier.weight(1f))
                            Stat("${quotes.size}", "Requests", Modifier.weight(1f))
                            Stat("${quotes.sumOf { it.quotes.size }}", "Replies", Modifier.weight(1f))
                        }
                    }
                }
            }
        }
        if (saved.isNotEmpty()) {
            item { Section("Saved cars", Icons.Outlined.Bookmark, "${saved.size}") }
            items(saved, key = { it.variantId + it.city }) { c ->
                Tile(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 5.dp).clickable { onModel(c.modelId) }, pad = 12) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        VehicleImage(vm.prefs.img(c.imageUrl, 480), c.model, Modifier.width(96.dp).aspectRatio(16 / 10f))
                        Spacer(Modifier.width(12.dp))
                        Column(Modifier.weight(1f)) {
                            Text("${c.brand} ${c.model}", style = MaterialTheme.typography.titleMedium, maxLines = 1, overflow = TextOverflow.Ellipsis)
                            Text("${c.variant} · ${c.city}", color = Mute, style = MaterialTheme.typography.bodySmall, maxLines = 1, overflow = TextOverflow.Ellipsis)
                            Text("Price tracked", color = Good, style = MaterialTheme.typography.labelMedium)
                        }
                        IconButton({ scope.launch { runCatching { vm.api.unsave(c.variantId, c.city) }; saved = saved - c } }) {
                            Icon(Icons.Outlined.Delete, "Remove", tint = Mute)
                        }
                    }
                }
            }
        }
        if (quotes.isNotEmpty()) {
            item { Section("My dealer quotes", Icons.Outlined.RequestQuote, "${quotes.size}") }
            items(quotes, key = { it.id }) { r ->
                Tile(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 5.dp), pad = 14) {
                    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Column(Modifier.weight(1f)) {
                                Text("${r.brand} ${r.model}", style = MaterialTheme.typography.titleMedium)
                                Text("${r.variant} · ${r.city}", color = Mute, style = MaterialTheme.typography.bodySmall)
                            }
                            Chip(if (r.quotes.isEmpty()) "Waiting" else "${r.quotes.size} quotes", if (r.quotes.isEmpty()) Amber else Good)
                        }
                        r.quotes.forEachIndexed { i, q ->
                            Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(12.dp)).background(if (i == 0) Good.copy(alpha = 0.10f) else Panel2).padding(10.dp),
                                verticalAlignment = Alignment.CenterVertically) {
                                Column(Modifier.weight(1f)) {
                                    Text(q.dealer, fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                                    Text(listOfNotNull(if (i == 0) "Lowest" else null, q.waitingWeeks?.let { "$it wk wait" }, q.validUntil?.let { "valid till $it" })
                                        .joinToString(" · "), color = Mute, style = MaterialTheme.typography.bodySmall)
                                }
                                Text(rupees(q.onRoadInr), fontWeight = FontWeight.Bold, color = if (i == 0) Good else Ink)
                            }
                        }
                    }
                }
            }
        }
        item { Section("Preferences", null, null) }
        item {
            Group {
                SettingRow(Icons.Outlined.LocationOn, Ignition, "City for prices", city, onClick = onCity)
                SettingRow(Icons.Outlined.Notifications, Amber, "Offers & launch alerts", "Manufacturer offers and newly listed models") {
                    Switch(alerts, { alerts = it; vm.prefs.alerts = it }, colors = SwitchDefaults.colors(checkedTrackColor = Ignition))
                }
                // Appearance: follow the phone, or always light / always dark
                val mode by ThemeMode.mode.collectAsStateWithLifecycle()
                SettingRow(Icons.Outlined.Palette, Electric, "Appearance", when (mode) { "light" -> "Light"; "dark" -> "Dark"; else -> "Same as phone" }) {
                    Row(Modifier.clip(RoundedCornerShape(50)).background(Panel2).padding(3.dp)) {
                        listOf("system" to "Auto", "light" to "Light", "dark" to "Dark").forEach { (k, l) ->
                            Text(l, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.SemiBold,
                                color = if (mode == k) Color.White else Mute,
                                modifier = Modifier.clip(RoundedCornerShape(50)).background(if (mode == k) Ignition else Color.Transparent)
                                    .clickable { ThemeMode.set(k) }.padding(horizontal = 10.dp, vertical = 6.dp))
                        }
                    }
                }
            }
        }
        item { Section("Help", null, null) }
        item {
            Group {
                SettingRow(Icons.AutoMirrored.Outlined.MenuBook, Electric, "Buying guide", "From quote to number plate, step by step", onClick = onGuide)
                SettingRow(Icons.Outlined.Verified, Good, "Where prices come from", "Manufacturers' own sites; taxes from your state's transport rules")
            }
        }
        if (acc != null) item {
            Spacer(Modifier.height(14.dp))
            Group {
                SettingRow(Icons.AutoMirrored.Outlined.Logout, Color(0xFFFF5C7A), "Sign out", null, titleColor = Color(0xFFFF5C7A), onClick = {
                    scope.launch { runCatching { vm.api.logout() }; vm.prefs.session = null; vm.prefs.setAccount(null) }
                })
            }
        }
        item {
            Text("OnRoad · honest on-road prices", color = Mute, style = MaterialTheme.typography.bodySmall,
                modifier = Modifier.fillMaxWidth().padding(top = 20.dp), textAlign = TextAlign.Center)
        }
    }
}

@Composable
private fun Stat(value: String, label: String, modifier: Modifier) = Column(
    modifier.clip(RoundedCornerShape(16.dp)).background(Panel2).padding(vertical = 12.dp),
    horizontalAlignment = Alignment.CenterHorizontally,
) {
    Text(value, style = MaterialTheme.typography.headlineSmall)
    Text(label, color = Mute, style = MaterialTheme.typography.bodySmall, maxLines = 1)
}

@Composable
private fun Shortcut(icon: ImageVector, label: String, tint: Color, modifier: Modifier, onClick: () -> Unit) = Column(
    modifier.clip(RoundedCornerShape(14.dp)).clickable(onClick = onClick).padding(vertical = 6.dp), horizontalAlignment = Alignment.CenterHorizontally,
) {
    Box(Modifier.size(48.dp).clip(RoundedCornerShape(16.dp)).background(tint.copy(alpha = 0.15f)), contentAlignment = Alignment.Center) {
        Icon(icon, null, tint = tint, modifier = Modifier.size(24.dp))
    }
    Spacer(Modifier.height(8.dp))
    Text(label, style = MaterialTheme.typography.labelMedium, textAlign = TextAlign.Center, maxLines = 2)
}

@Composable
private fun Section(title: String, icon: ImageVector?, count: String?) = Row(
    Modifier.padding(start = 20.dp, end = 20.dp, top = 22.dp, bottom = 8.dp), verticalAlignment = Alignment.CenterVertically,
) {
    icon?.let { Icon(it, null, tint = Ignition, modifier = Modifier.size(20.dp)); Spacer(Modifier.width(8.dp)) }
    Text(title, style = MaterialTheme.typography.titleLarge, modifier = Modifier.weight(1f))
    count?.let { Chip(it, Mute) }
}

@Composable
private fun Group(content: @Composable () -> Unit) = Column(
    Modifier.fillMaxWidth().padding(horizontal = 16.dp).clip(RoundedCornerShape(22.dp)).background(Panel).border(1.dp, Line, RoundedCornerShape(22.dp)),
) { content() }

@Composable
private fun SettingRow(icon: ImageVector, tint: Color, title: String, sub: String?, titleColor: Color = Ink,
                       onClick: (() -> Unit)? = null, trailing: (@Composable () -> Unit)? = null) = Row(
    Modifier.fillMaxWidth().then(if (onClick != null) Modifier.clickable(onClick = onClick) else Modifier).padding(horizontal = 14.dp, vertical = 14.dp),
    verticalAlignment = Alignment.CenterVertically,
) {
    Box(Modifier.size(40.dp).clip(RoundedCornerShape(12.dp)).background(tint.copy(alpha = 0.14f)), contentAlignment = Alignment.Center) {
        Icon(icon, null, tint = tint, modifier = Modifier.size(20.dp))
    }
    Spacer(Modifier.width(14.dp))
    Column(Modifier.weight(1f)) {
        Text(title, fontWeight = FontWeight.SemiBold, color = titleColor)
        sub?.let { Text(it, color = Mute, style = MaterialTheme.typography.bodySmall, maxLines = 2, overflow = TextOverflow.Ellipsis) }
    }
    if (trailing != null) trailing() else if (onClick != null) Icon(Icons.AutoMirrored.Outlined.KeyboardArrowRight, null, tint = Mute)
}
