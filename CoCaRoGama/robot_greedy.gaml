/**
* Name: robot_random 
* Author: ashfa
* Tags: CoCaRo
*/


model robot_greedy
import "robot_base.gaml"


species robot_greedy parent: robot_base {

    // ===== MOVE & SEARCH =====
    reflex search_box when: !empty(reachable_boxes) and battery > 0 {
    	// write reachable_boxes;
    	loop bx over: reachable_boxes {
    		int ant_reach_crit <- compute_anticipated_criticality(bx);  // ant. crit. of reachable box
    		
    		
			if carried_box = nil {
    			if targeted_box = nil {		// neither carrying, nor targeting
    				targeted_box <- bx;
    				targeted_box.owner <- self;
    			} else {					// not carrying but targeting
    				int my_target_box_crit <- compute_anticipated_criticality(targeted_box);
    				// check if this is a better box
    				if ant_reach_crit < my_target_box_crit {
    					targeted_box.owner <- nil;
    					targeted_box <- bx;
    					targeted_box.owner <- self;
    				}
    			}
    		} else {	// i carry a box
    			int my_carried_box_crit <- compute_anticipated_criticality(carried_box);
    			// check if this is a better box
    			if ant_reach_crit < my_carried_box_crit {
    				// drop the current box
    				carried_box.owner <-nil;		
    				carried_box <- nil;
    				// Target the new better box
    				targeted_box <- bx;
    				targeted_box.owner <- self;
    			}
    		}
    	}
    }

   

} 




