package com.onroad.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import retrofit2.HttpException

/** The server's message ({"detail": ...}) or a plain fallback. */
private fun Throwable.reason(fallback: String): String = (this as? HttpException)?.response()?.errorBody()?.string()
    ?.let { Regex("\"detail\"\\s*:\\s*\"([^\"]+)\"").find(it)?.groupValues?.get(1) } ?: fallback

/**
 * Account set-up after sign-up: 1) confirm the mobile number with an SMS code (one account per number, so showrooms only
 * get real requests), 2) budget and the kinds of cars you're looking at (Explore opens with them). Either step can wait.
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun AccountSetupScreen(onDone: () -> Unit, phoneOnly: Boolean = false, vm: BrowseVM = hiltViewModel()) {
    var step by remember { mutableIntStateOf(0) }
    var number by remember { mutableStateOf("") }
    var code by remember { mutableStateOf("") }
    var sentTo by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var wait by remember { mutableIntStateOf(0) }
    var budget by remember { mutableStateOf(vm.prefs.prefBudget) }
    var bodies by remember { mutableStateOf(vm.prefs.prefBodies) }
    val scope = rememberCoroutineScope()
    LaunchedEffect(wait) { if (wait > 0) { delay(1000); wait-- } }

    fun send() {
        busy = true; error = null
        scope.launch {
            runCatching { vm.api.phoneSend(com.onroad.app.data.PhoneIn(number)) }
                .onSuccess { sentTo = number; code = ""; wait = 30 }
                .onFailure { error = it.reason("Couldn't send the code. Try again in a minute.") }
            busy = false
        }
    }
    fun verify(c: String) {
        val to = sentTo ?: return
        busy = true; error = null
        scope.launch {
            runCatching { vm.api.phoneVerify(com.onroad.app.data.PhoneCodeIn(to, c)) }
                .onSuccess {
                    runCatching { vm.api.me() }.onSuccess { vm.prefs.setAccount(it) }
                    if (phoneOnly) onDone() else step = 1
                }
                .onFailure { error = it.reason("That code isn't right. Check the SMS and try again.") }
            busy = false
        }
    }

    Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).statusBarsPadding().navigationBarsPadding().imePadding()
        .verticalScroll(rememberScrollState()).padding(24.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        if (!phoneOnly) Text("Step ${step + 1} of 2", color = Mute, style = MaterialTheme.typography.labelLarge)
        if (step == 0) {
            Text("Confirm your mobile number", style = MaterialTheme.typography.headlineSmall)
            Text("Showrooms only see requests from verified buyers, and each number can have one OnRoad account. " +
                "Your number is never shown to showrooms.", color = Mute)
            if (sentTo == null) {
                OutlinedTextField(number, { v -> number = v.filter { it.isDigit() || it == '+' || it == ' ' }.take(16) }, Modifier.fillMaxWidth(),
                    label = { Text("Mobile number") }, placeholder = { Text("98765 43210") }, singleLine = true, shape = Corner,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone), enabled = !busy)
                Button(::send, Modifier.fillMaxWidth().height(52.dp), enabled = !busy && number.count { it.isDigit() } >= 10,
                    colors = ButtonDefaults.buttonColors(containerColor = Ignition), shape = Corner) {
                    Text(if (busy) "Sending…" else "Send code", fontWeight = FontWeight.SemiBold)
                }
            } else {
                Text("Enter the 6-digit code sent to $sentTo")
                OutlinedTextField(code, { v ->
                    code = v.filter { it.isDigit() }.take(6)
                    if (code.length == 6 && !busy) verify(code)
                }, Modifier.fillMaxWidth(), label = { Text("Code") }, singleLine = true, shape = Corner, enabled = !busy,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword))
                Button({ verify(code) }, Modifier.fillMaxWidth().height(52.dp), enabled = !busy && code.length == 6,
                    colors = ButtonDefaults.buttonColors(containerColor = Ignition), shape = Corner) {
                    Text(if (busy) "Checking…" else "Confirm", fontWeight = FontWeight.SemiBold)
                }
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    TextButton({ send() }, enabled = !busy && wait == 0) { Text(if (wait > 0) "Resend in ${wait}s" else "Resend code", color = Ignition) }
                    TextButton({ sentTo = null; error = null }, enabled = !busy) { Text("Edit number", color = Mute) }
                }
            }
            error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            TextButton({ if (phoneOnly) onDone() else step = 1 }, Modifier.fillMaxWidth()) { Text("Do this later", color = Mute) }
        } else {
            Text("What are you looking for?", style = MaterialTheme.typography.headlineSmall)
            Text("Explore opens with these picked. Change them any time.", color = Mute)
            Text("Budget (ex-showroom)", fontWeight = FontWeight.SemiBold)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("budget" to "Under ₹6 L", "middle" to "₹6–12 L", "upper-middle" to "₹12–20 L", "premium" to "₹20–40 L", "luxury" to "₹40 L +").forEach { (k, l) ->
                    Choice(l, budget == k) { budget = if (budget == k) null else k }
                }
            }
            Text("Car type", fontWeight = FontWeight.SemiBold)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                CAR_BODIES.forEach { b -> Choice(b, b in bodies) { bodies = if (b in bodies) bodies - b else bodies + b } }
            }
            Spacer(Modifier.height(8.dp))
            Button({ vm.prefs.prefBudget = budget; vm.prefs.prefBodies = bodies; onDone() }, Modifier.fillMaxWidth().height(52.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Ignition), shape = Corner) { Text("Start exploring", fontWeight = FontWeight.SemiBold) }
            TextButton(onDone, Modifier.fillMaxWidth()) { Text("Skip", color = Mute) }
        }
    }
}

@Composable
private fun Choice(label: String, on: Boolean, onClick: () -> Unit) {
    Text(label, color = if (on) Ignition else Ink, fontWeight = if (on) FontWeight.SemiBold else FontWeight.Normal,
        modifier = Modifier.clip(Corner).background(if (on) Ignition.copy(alpha = 0.10f) else Panel)
            .border(1.dp, if (on) Ignition else Line, Corner).clickable(onClick = onClick).padding(horizontal = 14.dp, vertical = 9.dp))
}
