package com.terrarium.app.ui.animations

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.Dp
import com.airbnb.lottie.compose.*

/**
 * Animation utilities for the Terrarium app.
 * Provides Compose-friendly animation helpers and Lottie animation management.
 */

// Animation file paths
object AnimationAssets {
    const val WATER_DROPLETS = "animations/water_droplets.json"
    const val PLANT_GROWTH = "animations/plant_growth.json"
    const val SPARKLES = "animations/sparkles.json"
    const val COIN_FLIP = "animations/coin_flip.json"
}

/**
 * Lottie animation state helper
 */
@Composable
fun rememberLottieAnimationState(
    assetPath: String,
    iterations: Int = LottieConstants.IterateForever,
    speed: Float = 1f
): LottieAnimationState {
    val composition by rememberLottieComposition(
        LottieCompositionSpec.Asset(assetPath)
    )
    
    val progress = animateLottieCompositionAsState(
        composition = composition,
        iterations = iterations,
        speed = speed
    )
    
    return remember(composition, progress) {
        LottieAnimationState(composition, progress.value)
    }
}

data class LottieAnimationState(
    val composition: LottieComposition?,
    val progress: Float
)

/**
 * Pulsing animation modifier
 */
@Composable
fun Modifier.pulseAnimation(
    pulseFraction: Float = 0.1f,
    durationMs: Int = 1000
): Modifier {
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    
    val scale by infiniteTransition.animateFloat(
        initialValue = 1f,
        targetValue = 1f + pulseFraction,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMs, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "scale"
    )
    
    return this.scale(scale)
}

/**
 * Bounce entrance animation
 */
@Composable
fun Modifier.bounceEntrance(
    visible: Boolean = true,
    durationMs: Int = 500
): Modifier {
    val scale by animateFloatAsState(
        targetValue = if (visible) 1f else 0f,
        animationSpec = spring(
            dampingRatio = Spring.DampingRatioMediumBouncy,
            stiffness = Spring.StiffnessLow
        ),
        label = "bounce"
    )
    
    return this.scale(scale)
}

/**
 * Fade in animation
 */
@Composable
fun Modifier.fadeInAnimation(
    visible: Boolean = true,
    durationMs: Int = 300
): Modifier {
    val alpha by animateFloatAsState(
        targetValue = if (visible) 1f else 0f,
        animationSpec = tween(durationMs),
        label = "alpha"
    )
    
    return this.alpha(alpha)
}

/**
 * Shimmer loading effect
 */
@Composable
fun Modifier.shimmerLoading(
    visible: Boolean = true,
    durationMs: Int = 1000
): Modifier {
    val infiniteTransition = rememberInfiniteTransition(label = "shimmer")
    
    val shimmerOffset by infiniteTransition.animateFloat(
        initialValue = -1000f,
        targetValue = 1000f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMs, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "shimmer"
    )
    
    return if (visible) {
        this.background(MaterialTheme.colorScheme.surfaceVariant)
        // Note: For full shimmer, use brush with gradient offset by shimmerOffset
    } else {
        this
    }
}

/**
 * XP gain animation - floating text effect
 */
@Composable
fun XpGainAnimation(
    xp: Int,
    visible: Boolean,
    onComplete: () -> Unit,
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "xp_float")
    
    val offsetY by animateFloatAsState(
        targetValue = if (visible) -50f else 0f,
        animationSpec = tween(1000, easing = FastOutSlowInEasing),
        label = "offset_y"
    )
    
    val alpha by animateFloatAsState(
        targetValue = if (visible) 0f else 1f,
        animationSpec = tween(1000, easing = LinearEasing),
        label = "alpha"
    )
    
    LaunchedEffect(visible) {
        if (visible) {
            kotlinx.coroutines.delay(1000)
            onComplete()
        }
    }
    
    Box(
        modifier = modifier
            .alpha(alpha)
    ) {
        // XP text would be displayed here with offset animation
    }
}

/**
 * Plant watering animation overlay
 */
@Composable
fun WateringAnimationOverlay(
    isPlaying: Boolean,
    onComplete: () -> Unit,
    modifier: Modifier = Modifier
) {
    val composition by rememberLottieComposition(
        LottieCompositionSpec.Asset(AnimationAssets.WATER_DROPLETS)
    )
    
    val progress by animateLottieCompositionAsState(
        composition = composition,
        iterations = 1,
        isPlaying = isPlaying,
        speed = 1f
    )
    
    LaunchedEffect(progress) {
        if (progress >= 1f && isPlaying) {
            onComplete()
        }
    }
    
    if (isPlaying) {
        LottieAnimation(
            composition = composition,
            progress = { progress },
            modifier = modifier
        )
    }
}

/**
 * Plant growth transition animation
 */
@Composable
fun PlantGrowthAnimation(
    isPlaying: Boolean,
    modifier: Modifier = Modifier
) {
    val composition by rememberLottieComposition(
        LottieCompositionSpec.Asset(AnimationAssets.PLANT_GROWTH)
    )
    
    val progress by animateLottieCompositionAsState(
        composition = composition,
        iterations = 1,
        isPlaying = isPlaying,
        speed = 1f
    )
    
    LottieAnimation(
        composition = composition,
        progress = { progress },
        modifier = modifier
    )
}

/**
 * Sparkles animation for XP gain
 */
@Composable
fun SparklesAnimation(
    isPlaying: Boolean,
    modifier: Modifier = Modifier
) {
    val composition by rememberLottieComposition(
        LottieCompositionSpec.Asset(AnimationAssets.SPARKLES)
    )
    
    val progress by animateLottieCompositionAsState(
        composition = composition,
        iterations = 1,
        isPlaying = isPlaying,
        speed = 1f
    )
    
    LottieAnimation(
        composition = composition,
        progress = { progress },
        modifier = modifier
    )
}

/**
 * Coin flip animation for purchases
 */
@Composable
fun CoinFlipAnimation(
    isPlaying: Boolean,
    modifier: Modifier = Modifier
) {
    val composition by rememberLottieComposition(
        LottieCompositionSpec.Asset(AnimationAssets.COIN_FLIP)
    )
    
    val progress by animateLottieCompositionAsState(
        composition = composition,
        iterations = 1,
        isPlaying = isPlaying,
        speed = 1f
    )
    
    LottieAnimation(
        composition = composition,
        progress = { progress },
        modifier = modifier
    )
}

/**
 * Scale press effect for buttons
 */
@Composable
fun Modifier.scaleOnPress(
    pressed: Boolean,
    scale: Float = 0.95f
): Modifier {
    val scaleValue by animateFloatAsState(
        targetValue = if (pressed) scale else 1f,
        animationSpec = spring(stiffness = Spring.StiffnessHigh),
        label = "scale_press"
    )
    
    return this.scale(scaleValue)
}

/**
 * Color transition for status changes
 */
@Composable
fun animateStatusColor(
    isActive: Boolean,
    activeColor: Color,
    inactiveColor: Color
): Color {
    return animateColorAsState(
        targetValue = if (isActive) activeColor else inactiveColor,
        animationSpec = tween(300),
        label = "status_color"
    ).value
}