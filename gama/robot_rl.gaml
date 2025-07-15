model robot_rl

import "robot_base.gaml"



species robot_rl parent: robot_base {
    
    // ===== ENHANCED RL ATTRIBUTES =====
    float epsilon <- 0.3;  // Higher exploration initially
    float learning_rate <- 0.1;
    float discount_factor <- 0.9;
    
    // Neural network-like Q-table with feature-based states
    map<string, float> q_weights <- map<string, float>([]);
    
    // Previous state features and action for learning
    list<float> previous_state_features <- [];
    int previous_action_index <- -1;
    float previous_reward <- 0.0;
    
    // ===== ENHANCED STATE FEATURES =====
    list<float> extract_box_features(box_ bx) {
        list<float> features <- [];
        
        if (bx = nil or bx.myCell = nil) {
            // Return zero features for nil box or invalid box
            return [0.0, 0.0, 0.0, 0.0, 0.0];
        }
        
        // Distance feature (normalized)
        float distance <- self distance_to bx;
        features << (distance / 100.0);  // Assuming max distance ~100
        
        // Criticality feature
        float anticipated_crit <- compute_anticipated_criticality(bx);
        features << (anticipated_crit / max_criticality);
        
        // Color match feature
        features << (bx.color = self.color ? 1.0 : 0.0);
        
        // Box availability (is it owned?)
        features << (bx.owner = nil ? 1.0 : 0.0);
        
        // Competition feature (safer calculation)
        int competitors <- 0;
        loop rb over: robot_base {
            if (rb != nil and rb.reachable_boxes != nil) {
                bool has_box <- false;
                loop rb_box over: rb.reachable_boxes {
                    if (rb_box = bx) {
                        has_box <- true;
                        break;
                    }
                }
                if (has_box) {
                    competitors <- competitors + 1;
                }
            }
        }
        features << min(1.0, competitors / 5.0);
        
        return features;
    }
    
    list<float> get_state_features {
        list<float> features <- [];
        
        // Robot state
        features << (battery / max_battery);
        features << (criticality / max_criticality);
        features << (carried_box != nil ? 1.0 : 0.0);
        
        // Environment state - count valid reachable boxes
        int valid_count <- 0;
        loop bx over: reachable_boxes {
            if (bx != nil and bx.myCell != nil) {
                valid_count <- valid_count + 1;
            }
        }
        features << min(1.0, valid_count / 10.0);
        
        // If we have a current target, include its features
        if (targeted_box != nil and targeted_box.myCell != nil) {
            features <- features + extract_box_features(targeted_box);
        } else {
            // Pad with zeros if no target
            features <- features + [0.0, 0.0, 0.0, 0.0, 0.0];
        }
        
        return features;
    }
    
    // ===== Q-VALUE ESTIMATION WITH FUNCTION APPROXIMATION =====
    float estimate_q_value(list<float> state_features, int action_index) {
        float q_value <- 0.0;
        
        loop i from: 0 to: length(state_features) - 1 {
            string weight_key <- "w_" + i + "_" + action_index;
            if (!(weight_key in q_weights)) {
                q_weights[weight_key] <- rnd(-0.1, 0.1);  // Small random initialization
            }
            q_value <- q_value + (state_features[i] * q_weights[weight_key]);
        }
        
        return q_value;
    }
    
    // ===== ENHANCED REWARD FUNCTION =====
    float compute_box_reward {
        float reward <- 0.0;
        
        // Reward for picking up a box
        if (carried_box != nil and previous_state_features[2] = 0.0) {
            // Color bonus
            if (carried_box.color = self.color) {
                reward <- reward + 10.0;
            } else {
                reward <- reward + 3.0;
            }
            
            // Efficiency bonus (lower criticality is better)
            float efficiency <- 1.0 - (compute_anticipated_criticality(carried_box) / max_criticality);
            reward <- reward + (efficiency * 5.0);
        }
        
        // Penalty for battery depletion
        if (battery < (max_battery * 0.2)) {
            reward <- reward - 2.0;
        }
        
        // Small penalty for time without progress
        if (targeted_box = nil and carried_box = nil and !empty(reachable_boxes)) {
            reward <- reward - 0.1;
        }
        
        return reward;
    }
    
    // ===== BOX SELECTION ACTIONS =====
    box_ select_box_by_action(int action_index) {
        // More robust nil filtering with explicit checks
        list<box_> valid_boxes <- [];
        loop bx over: reachable_boxes {
            if (bx != nil and bx.myCell != nil) {
                valid_boxes << bx;
            }
        }
        
        if (empty(valid_boxes)) { return nil; }
        
        switch action_index {
            match 0 { // Best criticality - safe version
                box_ best_box <- nil;
                float best_score <- max_criticality + 1.0;
                loop bx over: valid_boxes {
                    if (bx != nil) {
                        float score <- compute_anticipated_criticality(bx);
                        if (score < best_score) {
                            best_score <- score;
                            best_box <- bx;
                        }
                    }
                }
                return best_box;
            }
            match 1 { // Nearest - safe version
                box_ nearest_box <- nil;
                float min_distance <- 999999.0;
                loop bx over: valid_boxes {
                    if (bx != nil) {
                        float dist <- self distance_to bx;
                        if (dist < min_distance) {
                            min_distance <- dist;
                            nearest_box <- bx;
                        }
                    }
                }
                return nearest_box;
            }
            match 2 { // Best color match - safe version
                list<box_> matching <- [];
                loop bx over: valid_boxes {
                    if (bx != nil and bx.color = self.color) {
                        matching << bx;
                    }
                }
                
                if (!empty(matching)) {
                    box_ nearest_match <- nil;
                    float min_distance <- 999999.0;
                    loop bx over: matching {
                        if (bx != nil) {
                            float dist <- self distance_to bx;
                            if (dist < min_distance) {
                                min_distance <- dist;
                                nearest_match <- bx;
                            }
                        }
                    }
                    return nearest_match;
                } else {
                    // Fall back to best criticality
                    box_ best_box <- nil;
                    float best_score <- max_criticality + 1.0;
                    loop bx over: valid_boxes {
                        if (bx != nil) {
                            float score <- compute_anticipated_criticality(bx);
                            if (score < best_score) {
                                best_score <- score;
                                best_box <- bx;
                            }
                        }
                    }
                    return best_box;
                }
            }
            match 3 { // Balanced score - safe version
                box_ best_box <- nil;
                float best_score <- 999999.0;
                loop bx over: valid_boxes {
                    if (bx != nil) {
                        float crit_score <- compute_anticipated_criticality(bx) / max_criticality;
                        float dist_score <- (self distance_to bx) / 50.0;
                        float color_bonus <- (bx.color = self.color) ? 0.3 : 0.0;
                        float total_score <- crit_score + dist_score - color_bonus;
                        
                        if (total_score < best_score) {
                            best_score <- total_score;
                            best_box <- bx;
                        }
                    }
                }
                return best_box;
            }
            default { 
                return !empty(valid_boxes) ? valid_boxes[0] : nil;
            }
        }
    }
    
    // ===== MAIN RL DECISION REFLEX =====
    reflex rl_box_selection when: battery > 0 {
        list<float> current_state <- get_state_features();
        float current_reward <- compute_box_reward();
        
        // Q-learning update
        if (!empty(previous_state_features) and previous_action_index != -1) {
            float old_q <- estimate_q_value(previous_state_features, previous_action_index);
            
            // Find best Q-value for current state
            float max_q <- estimate_q_value(current_state, 0);
            loop i from: 1 to: 3 {
                float q_val <- estimate_q_value(current_state, i);
                if (q_val > max_q) { max_q <- q_val; }
            }
            
            float td_error <- current_reward + discount_factor * max_q - old_q;
            
            // Update weights
            loop i from: 0 to: length(previous_state_features) - 1 {
                string weight_key <- "w_" + i + "_" + previous_action_index;
                q_weights[weight_key] <- q_weights[weight_key] + 
                    learning_rate * td_error * previous_state_features[i];
            }
        }
        
        // Action selection (only when free to choose)
        // More robust nil filtering
        list<box_> valid_reachable <- [];
        loop bx over: reachable_boxes {
            if (bx != nil and bx.myCell != nil) {
                valid_reachable << bx;
            }
        }
        
        if (targeted_box = nil and carried_box = nil and !empty(valid_reachable)) {
            int action_idx;
            
            if (rnd(1.0) < epsilon) {
                // Explore
                action_idx <- rnd(3);
            } else {
                // Exploit - choose best action
                action_idx <- 0;
                float best_q <- estimate_q_value(current_state, 0);
                loop i from: 1 to: 3 {
                    float q_val <- estimate_q_value(current_state, i);
                    if (q_val > best_q) {
                        best_q <- q_val;
                        action_idx <- i;
                    }
                }
            }
            
            // Execute action
            box_ selected_box <- select_box_by_action(action_idx);
            if (selected_box != nil and selected_box.owner = nil) {
                targeted_box <- selected_box;
                targeted_box.owner <- self;
                previous_action_index <- action_idx;
            }
        }
        
        // Store state for next update
        previous_state_features <- current_state;
        previous_reward <- current_reward;
        
        // Decay exploration
        epsilon <- max(0.05, epsilon * 0.9995);
    }
    
    // ===== BOX SWITCHING LOGIC =====
    reflex rl_box_switching when: battery > 0 {
        // More robust nil filtering
        list<box_> valid_reachable <- [];
        loop bx over: reachable_boxes {
            if (bx != nil and bx.myCell != nil) {
                valid_reachable << bx;
            }
        }
        
        if (empty(valid_reachable)) { return; }
        
        box_ current_focus <- (carried_box != nil) ? carried_box : targeted_box;
        
        if (current_focus != nil) {
            // Check if there's a significantly better box available
            float current_score <- compute_anticipated_criticality(current_focus);
            
            // Find best available box manually (safe approach)
            box_ best_available <- nil;
            float best_score <- max_criticality + 1.0;
            loop bx over: valid_reachable {
                if (bx != nil and bx.owner = nil) {
                    float score <- compute_anticipated_criticality(bx);
                    if (score < best_score) {
                        best_score <- score;
                        best_available <- bx;
                    }
                }
            }
            
            if (best_available != nil) {
                // Switch if the improvement is significant
                if (best_score < (current_score * 0.7)) {  // 30% improvement threshold
                    if (carried_box != nil) {
                        carried_box.owner <- nil;
                        carried_box <- nil;
                    } else {
                        targeted_box.owner <- nil;
                        targeted_box <- nil;
                    }
                    
                    targeted_box <- best_available;
                    targeted_box.owner <- self;
                }
            }
        }
    }
}