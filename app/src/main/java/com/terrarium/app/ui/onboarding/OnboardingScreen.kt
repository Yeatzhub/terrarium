package com.terrarium.app.ui.onboarding

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.terrarium.app.data.model.JarType

/**
 * Onboarding tutorial screen with 5 steps.
 * Guides new users through the game mechanics.
 */

data class OnboardingPage(
    val emoji: String,
    val title: String,
    val description: String,
    val details: List<String>
)

private val onboardingPages = listOf(
    OnboardingPage(
        emoji = "🌿",
        title = "Welcome to Terrarium!",
        description = "Create your own miniature garden world",
        details = listOf(
            "Grow virtual plants in beautiful glass jars",
            "Collect rare and legendary species",
            "Share your garden with friends"
        )
    ),
    OnboardingPage(
        emoji = "🫙",
        title = "Choose Your First Jar",
        description = "Your terrarium awaits!",
        details = listOf(
            "Small Jar - Perfect for beginners (3 plants)",
            "Start with your favorite plant type",
            "Add decorative layers for bonus XP"
        )
    ),
    OnboardingPage(
        emoji = "🌱",
        title = "Plant Your First Seed",
        description = "Every garden starts with a single seed",
        details = listOf(
            "Select a seed from your inventory",
            "Place it in your terrarium",
            "Watch it grow over time!"
        )
    ),
    OnboardingPage(
        emoji = "💧",
        title = "Care for Your Plants",
        description = "Keep your plants happy and healthy",
        details = listOf(
            "Water plants when moisture is low",
            "Check on them daily for bonus XP",
            "Propagate mature plants to create cuttings"
        )
    ),
    OnboardingPage(
        emoji = "⭐",
        title = "Earn XP & Level Up!",
        description = "Complete daily tasks to grow your skills",
        details = listOf(
            "Watering plants gives XP",
            "Completing daily tasks earns coins",
            "Level up to unlock rare plants & new jars!"
        )
    )
)

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun OnboardingScreen(
    onComplete: () -> Unit
) {
    val pagerState = rememberPagerState(pageCount = { onboardingPages.size })
    val currentPage = pagerState.currentPage
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    colors = listOf(
                        MaterialTheme.colorScheme.primaryContainer,
                        MaterialTheme.colorScheme.background
                    )
                )
            ),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Skip button (top right)
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.End
        ) {
            TextButton(onClick = onComplete) {
                Text("Skip", color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f))
            }
        }
        
        // Page content
        HorizontalPager(
            state = pagerState,
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterHorizontally
        ) { page ->
            OnboardingPageContent(
                page = onboardingPages[page],
                isVisible = currentPage == page
            )
        }
        
        // Page indicators
        Row(
            modifier = Modifier.padding(16.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            repeat(onboardingPages.size) { index ->
                PageIndicator(
                    isSelected = currentPage == index,
                    onClick = {
                        // Could animate to page programmatically
                    }
                )
            }
        }
        
        // Navigation buttons
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp, vertical = 16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Back button
            if (currentPage > 0) {
                OutlinedButton(
                    onClick = {
                        // Navigate back would need coroutine scope
                    },
                    enabled = currentPage > 0
                ) {
                    Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("Back")
                }
            } else {
                Spacer(modifier = Modifier.width(80.dp))
            }
            
            // Next/Complete button
            val isLastPage = currentPage == onboardingPages.lastIndex
            
            Button(
                onClick = onComplete,
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.primary
                )
            ) {
                if (isLastPage) {
                    Text("Get Started!")
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("🎉")
                } else {
                    Text("Next")
                    Spacer(modifier = Modifier.width(4.dp))
                    Icon(Icons.AutoMirrored.Filled.ArrowForward, contentDescription = "Next")
                }
            }
        }
        
        Spacer(modifier = Modifier.height(24.dp))
    }
}

@Composable
private fun OnboardingPageContent(
    page: OnboardingPage,
    isVisible: Boolean
) {
    val animatedAlpha by animateFloatAsState(
        targetValue = if (isVisible) 1f else 0.3f,
        animationSpec = tween(300),
        label = "alpha"
    )
    
    val animatedScale by animateFloatAsState(
        targetValue = if (isVisible) 1f else 0.9f,
        animationSpec = spring(dampingRatio = Spring.DampingRatioMediumBouncy),
        label = "scale"
    )
    
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 32.dp)
            .alpha(animatedAlpha)
            .scale(animatedScale),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Large emoji
        Text(
            text = page.emoji,
            fontSize = 80.sp,
            modifier = Modifier.padding(bottom = 24.dp)
        )
        
        // Title
        Text(
            text = page.title,
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.onBackground,
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(12.dp))
        
        // Description
        Text(
            text = page.description,
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onBackground.copy(alpha = 0.7f),
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(32.dp))
        
        // Details card
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
            )
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                page.details.forEach { detail ->
                    Row(
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "✓",
                            color = MaterialTheme.colorScheme.primary,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(end = 8.dp)
                        )
                        Text(
                            text = detail,
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun PageIndicator(
    isSelected: Boolean,
    onClick: () -> Unit
) {
    val size by animateDpAsState(
        targetValue = if (isSelected) 12.dp else 8.dp,
        animationSpec = spring(dampingRatio = Spring.DampingRatioMediumBouncy),
        label = "indicator_size"
    )
    
    val color by animateColorAsState(
        targetValue = if (isSelected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.3f),
        animationSpec = tween(300),
        label = "indicator_color"
    )
    
    Box(
        modifier = Modifier
            .size(size)
            .clip(CircleShape)
            .background(color)
    )
}

@Composable
fun JarSelectionPreview(
    jarType: JarType,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = when (jarType) {
                    JarType.SMALL -> "🫙"
                    JarType.MEDIUM -> "🏺"
                    JarType.ROUND -> "🫗"
                    JarType.TALL -> "🏺"
                    JarType.WIDE -> "🥣"
                },
                fontSize = 48.sp
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "${jarType.name.lowercase().capitalize()} Jar",
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = "Capacity: ${when (jarType) {
                    JarType.SMALL -> 3
                    JarType.MEDIUM -> 5
                    JarType.ROUND -> 4
                    JarType.TALL -> 6
                    JarType.WIDE -> 7
                }} plants",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

// Preview for onboarding (used in development)
@Composable
fun OnboardingPreview() {
    MaterialTheme {
        OnboardingScreen(onComplete = {})
    }
}