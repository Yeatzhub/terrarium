package com.terrarium.app.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.terrarium.app.data.model.InventoryItem
import com.terrarium.app.data.repository.InventoryRepository
import com.terrarium.app.data.repository.UserRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class InventoryViewModel @Inject constructor(
    private val inventoryRepository: InventoryRepository,
    private val userRepository: UserRepository
) : ViewModel() {
    
    private val _userId = MutableStateFlow(1L) // Default user ID
    
    val inventory: StateFlow<List<InventoryItem>> = _userId
        .flatMapLatest { userId ->
            inventoryRepository.getInventoryForUser(userId)
        }
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())
    
    init {
        // Load current user
        viewModelScope.launch {
            userRepository.getCurrentUser()?.let { user ->
                _userId.value = user.id
            }
        }
    }
}