package com.onroad.app.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.mutableStateOf
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewmodel.compose.viewModel

/** Screen state that must survive opening a car and coming back (filters, sort, tab). It lives in a ViewModel scoped
 *  to the screen's back-stack entry, so it is kept while the screen is in the history and dropped when it leaves. */
class KeepVM : ViewModel() {
    val states = HashMap<String, MutableState<*>>()
}

@Suppress("UNCHECKED_CAST")
@Composable
fun <T> rememberKept(key: String, init: () -> T): MutableState<T> {
    val vm: KeepVM = viewModel()
    return vm.states.getOrPut(key) { mutableStateOf(init()) } as MutableState<T>
}
