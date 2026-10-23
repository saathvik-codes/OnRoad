package com.onroad.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.onroad.app.data.Breakdown
import kotlinx.coroutines.launch

/** Any quote → itemised on-road price for the chosen city, using the same state rules as the website. */
@Composable
fun CalculatorScreen(onBack: () -> Unit, vm: BrowseVM = hiltViewModel()) {
    val city by vm.prefs.city.collectAsStateWithLifecycle()
    var type by remember { mutableStateOf("car") }
    var price by remember { mutableStateOf("") }
    var cc by remember { mutableStateOf("") }
    var fuel by remember { mutableStateOf("Petrol") }
    var result by remember { mutableStateOf<Breakdown?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val fuels = if (type == "bike") listOf("Petrol", "Electric") else listOf("Petrol", "Diesel", "CNG", "Hybrid", "Electric")

    @Composable
    fun pills(options: List<Pair<String, String>>, sel: String, onSel: (String) -> Unit) =
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            options.forEach { (k, l) ->
                Text(l, style = MaterialTheme.typography.labelLarge, color = if (sel == k) Color.White else Mute,
                    modifier = Modifier.clip(RoundedCornerShape(50)).background(if (sel == k) Ignition else Panel2)
                        .clickable { onSel(k) }.padding(horizontal = 14.dp, vertical = 8.dp))
            }
        }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).statusBarsPadding().navigationBarsPadding()) {
        Row(Modifier.padding(start = 4.dp, top = 6.dp), verticalAlignment = Alignment.CenterVertically) {
            IconButton(onBack) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "Back") }
            Column { Text("On-road calculator", style = MaterialTheme.typography.titleLarge); Text("Rules for $city", color = Mute) }
        }
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            pills(listOf("car" to "Car", "bike" to "Bike / scooter"), type) { type = it; if (fuel !in fuels) fuel = "Petrol"; result = null }
            OutlinedTextField(price, { price = it.filter(Char::isDigit).take(10) }, Modifier.fillMaxWidth(), singleLine = true,
                label = { Text("Ex-showroom price (₹) from the quote") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
            pills(fuels.map { it to it }, fuel) { fuel = it; result = null }
            if (fuel != "Electric") OutlinedTextField(cc, { cc = it.filter(Char::isDigit).take(4) }, Modifier.fillMaxWidth(), singleLine = true,
                label = { Text("Engine (cc), optional") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
            Button(onClick = {
                val ex = price.toLongOrNull()
                if (ex == null || ex <= 20_000) { error = "Enter the ex-showroom price"; return@Button }
                busy = true; error = null
                scope.launch {
                    runCatching { vm.api.quick(ex, city, fuel, cc.toIntOrNull(), type) }
                        .onSuccess { result = it }.onFailure { error = "Couldn't calculate. Check your connection." }
                    busy = false
                }
            }, Modifier.fillMaxWidth().height(52.dp), enabled = !busy, colors = ButtonDefaults.buttonColors(containerColor = Ignition)) {
                Text(if (busy) "Calculating…" else "Show on-road price", fontWeight = FontWeight.SemiBold)
            }
            error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            result?.let { b ->
                Tile(Modifier.fillMaxWidth()) {
                    Column {
                        Text("ON-ROAD IN ${b.stateName.uppercase()}", style = MaterialTheme.typography.labelSmall, color = Mute)
                        Text(rupees(b.totalInr - b.refundableInr), style = MaterialTheme.typography.displaySmall)
                        if (b.refundableInr > 0) Text("+ ${rupees(b.refundableInr)} TCS, which you get back in your tax return", color = Mute)
                        Spacer(Modifier.height(10.dp))
                        b.lines.filter { !it.refundable }.forEach { l ->
                            Row(Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
                                Column(Modifier.weight(1f)) {
                                    Text(l.label + if (l.optional) " (optional)" else "", style = MaterialTheme.typography.titleMedium)
                                    Text(l.basis, color = Mute, style = MaterialTheme.typography.bodyMedium)
                                }
                                Text(if (l.amountInr != null) rupees(l.amountInr) else "—", fontWeight = FontWeight.SemiBold)
                            }
                        }
                        Text("Anything else on a dealer quote (handling, ‘essential kit’, number-plate fee) is not part of the legal price.",
                            color = Amber, style = MaterialTheme.typography.bodyMedium)
                    }
                }
            }
        }
    }
}
