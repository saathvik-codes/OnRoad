package com.onroad.app.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import kotlin.math.roundToLong

/**
 * EV vs petrol running cost: what a month of driving costs each way, and how long the EV's higher price takes to pay
 * back. Every input is editable; the defaults are typical figures for a compact SUV, labelled as such.
 */
@Composable
fun EvCostCard() {
    var km by remember { mutableStateOf("1200") }          // per month
    var petrol by remember { mutableStateOf("107") }      // ₹ per litre
    var kmpl by remember { mutableStateOf("15") }
    var unit by remember { mutableStateOf("8") }          // ₹ per kWh at home
    var kmpkwh by remember { mutableStateOf("7") }
    var premium by remember { mutableStateOf("250000") }  // how much more the EV costs on-road

    @Composable fun field(v: String, set: (String) -> Unit, label: String, m: Modifier) = OutlinedTextField(v,
        { set(it.filter { c -> c.isDigit() || c == '.' }.take(8)) }, m, singleLine = true, label = { Text(label) },
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal))

    Tile(Modifier.fillMaxWidth()) {
        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("EV or petrol: running cost", style = MaterialTheme.typography.titleLarge)
            Art("hero-ev-cost", Modifier.fillMaxWidth().height(120.dp))
            field(km, { km = it }, "Km you drive a month", Modifier.fillMaxWidth())
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                field(petrol, { petrol = it }, "Petrol ₹/litre", Modifier.weight(1f))
                field(kmpl, { kmpl = it }, "Mileage km/litre", Modifier.weight(1f))
            }
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                field(unit, { unit = it }, "Electricity ₹/unit", Modifier.weight(1f))
                field(kmpkwh, { kmpkwh = it }, "EV km per unit", Modifier.weight(1f))
            }
            field(premium, { premium = it }, "Extra price of the EV (₹)", Modifier.fillMaxWidth())

            val k = km.toDoubleOrNull(); val p = petrol.toDoubleOrNull(); val m = kmpl.toDoubleOrNull()
            val u = unit.toDoubleOrNull(); val e = kmpkwh.toDoubleOrNull(); val extra = premium.toDoubleOrNull() ?: 0.0
            if (k != null && p != null && m != null && u != null && e != null && m > 0 && e > 0) {
                val petrolMonth = k / m * p
                val evMonth = k / e * u
                val save = petrolMonth - evMonth
                Row(Modifier.fillMaxWidth()) {
                    Column(Modifier.weight(1f)) { Text("Petrol / month", color = Mute); Text(rupees(petrolMonth.roundToLong()), style = MaterialTheme.typography.titleLarge) }
                    Column(Modifier.weight(1f)) { Text("EV / month", color = Mute); Text(rupees(evMonth.roundToLong()), style = MaterialTheme.typography.titleLarge, color = Good) }
                }
                Text(if (save > 0) "The EV saves ${rupees(save.roundToLong())} a month, ${rupees((save * 12).roundToLong())} a year." +
                        (if (extra > 0) " It pays back its extra price in about ${"%.1f".format(extra / (save * 12))} years." else "")
                    else "At these numbers petrol costs less to run.", style = MaterialTheme.typography.bodyLarge)
                Text("Charging at public fast chargers costs ₹18–25 a unit, which cuts the saving. Insurance and service aren't included.",
                    color = Mute, style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}
