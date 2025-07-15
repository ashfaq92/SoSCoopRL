/**
* Name: robotbase
* Based on the internal empty template. 
* Author: ashfa
* Tags: 
*/


model robot_base

/* Insert your model definition here */


import "cell_.gaml"
import "nest.gaml"
import "box_.gaml"


species robot_base skills: [moving] {
    // ===== COMMON ATTRIBUTES =====
    int criticality <- 0 update: max_criticality - battery max: max_criticality;
	int min_criticality <- min_battery;
    int max_criticality <- max_battery;
    int max_battery <- 300;
    int min_battery <- 0;
    int initial_battery <- max_battery;
    int battery_consum <- 1;
    
	int reward <- int((2 * max_battery) / 3);
    int reduced_reward <- int(0.2 * reward);
    int battery <- initial_battery min: min_battery max: max_battery; 
    point previous_location <- location;
    nest target_nest <- nil;
    box_ carried_box <- nil;
    box_ targeted_box <- nil;
    list<box_> reachable_boxes update: (box_ where (myCell.neighbors_at_robot_vision contains each.myCell));  
    
    
    
    rgb color;
    cell myCell update: cell closest_to self;

    // ===== COMMON INITIALIZATION =====
    init {
        speed <- 1.0;
        
        list<cell> free_cells <- cell where (length(agents_inside(each)) = 0);    
        if (!empty(free_cells)) {
            location <- one_of(free_cells).location;
        } else {
        	write "couldn't find empty cell for robot!";
        	ask world { do pause; }
        }
    }
    
    // ===== COMMON ACTIONS =====
    int colors_reward_efficiency(rgb box_color) {
        if (box_color=color) {
            return reward;
        } else {
            return reduced_reward;
        }
    }
    
    reflex debug {
//    	write reachable_boxes;
//    	ask world {do pause; }
    }
    
    // ===== Calculate ANTICIPATED Criticality =====
	int compute_anticipated_criticality (box_ box_to_take) {
		int dist_box_to_me <- abs(box_to_take.myCell.grid_x - self.myCell.grid_x) + abs(box_to_take.myCell.grid_y - self.myCell.grid_y);
		nest nest_cell <- nest first_with (each.color = box_to_take.color);
		int dist_robot_to_nest <- abs(nest_cell.myCell.grid_x - self.myCell.grid_x) + abs(nest_cell.myCell.grid_y - self.myCell.grid_y);
		int anticipated_battery_before_reward <- battery - (dist_box_to_me + dist_robot_to_nest) * battery_consum;
		
		if anticipated_battery_before_reward < 0 {
			anticipated_battery_before_reward <- 0;
		}
				
		int anticipated_battery <- anticipated_battery_before_reward + colors_reward_efficiency(box_to_take.color);
		
		if anticipated_battery < min_battery or anticipated_battery_before_reward = 0 {
			return max_criticality;
		} else if anticipated_battery > max_battery {
			return min_criticality;
		} else {
			return max_criticality - anticipated_battery;
		}
	}
    
    // ===== COMMON REFLEXES =====
    reflex update_battery when: battery > 0 {
        bool moved_step <- (location != previous_location);
        if (moved_step) {
            battery <- battery - battery_consum;            
        }
        previous_location <- location;
    }
    
    reflex update_speed {
    	if battery <= max_battery and battery >= (2 * max_battery / 3) {
    		speed <- 1.0;	
    	} else if battery < (2 * max_battery / 3) and battery >= (1 * max_battery / 3) {
    		speed <- 1.0 / 2.0;
    	} else if  battery < (1 * max_battery / 3) and battery > 0 {
    		speed <- 1.0 / 3.0;
    	} else {
    		speed <- 0.0;
    	}
    }
    
     reflex basic_move when: targeted_box=nil and carried_box=nil and battery > 0 {
        do wander amplitude: 30.0;        
    }
    
    // target random box is different for each robot type
    
   reflex go_to_target_box when: targeted_box != nil and battery > 0 {
        path path_followed <- goto(target: targeted_box.location, on: cell, return_path: true);
    }
    
    
    
    reflex take_box when: targeted_box!=nil and targeted_box.myCell=myCell and battery > 0 {
        carried_box <- targeted_box;
        targeted_box <- nil;
    }

    reflex carry_box_to_nest when: carried_box != nil and battery > 0 {
    	if (!dead(carried_box)) {    		
        	target_nest <- nest first_with (each.color = carried_box.color);
        	do goto target: target_nest on: cell return_path: true;
    	} else {
    		carried_box <- nil;
    	}
    }
    
    reflex update_carried_box_position when: carried_box != nil and battery > 0 {
        carried_box.myCell <- myCell;
        carried_box.location <- location;
    }
    
//    reflex drop_box_in_nest when: carried_box != nil and target_nest != nil and battery > 0 {
//        if (myCell = target_nest.myCell) {
//            target_nest.deposited_boxes <- target_nest.deposited_boxes + 1;
//            battery <- battery + colors_reward_efficiency(carried_box.color);
//            
//            // Remove this box from all robots' references before killing it
//            box_ box_to_remove <- carried_box;
//            
//            ask agents where (each is robot_base) {
//			    if targeted_box = box_to_remove {
//			        targeted_box <- nil;
//			        write 'targeted_box cleared';
//			    }
//			    if carried_box = box_to_remove {
//			    	carried_box <- nil;
//			    	write 'carried_box cleared';
//			    }
//			}
//            
//            ask box_to_remove { do die; }
//            carried_box <- nil;
//            target_nest <- nil;
//        } else {
//            do goto target: target_nest on: cell return_path: true speed: float(robot_speed);
//        }
//    }

//	reflex drop_box_in_nest when: carried_box != nil and target_nest != nil and battery > 0 {
//	        if (myCell = target_nest.myCell) {
//	            target_nest.deposited_boxes <- target_nest.deposited_boxes + 1;
//	            battery <- battery + colors_reward_efficiency(carried_box.color);
//	
//	            ask agents where (each is robot_base and each != self) {
//	            
//				    if targeted_box = myself.carried_box {
//				        targeted_box <- nil;
//				    }
//				    if carried_box = myself.carried_box{
//				    	carried_box <- nil;
//				    }
//				}
//	            
//	            ask carried_box { do die; }
//	            carried_box <- nil;
//	            target_nest <- nil;
//	        } else {
//	            do goto target: target_nest on: cell return_path: true speed: float(robot_speed);
//	        }
//	    }

		reflex drop_box_in_nest when: carried_box != nil and target_nest != nil and battery > 0 and !dead(carried_box) {
	        if myCell = carried_box.myCell and myCell = target_nest.myCell and carried_box.myCell = target_nest.myCell {	// Overkill max paranoia triple-sure is better than sorry!
	            
	            battery <- battery + colors_reward_efficiency(carried_box.color);
	            
                box_ box_to_remove <- carried_box;	
	
	            ask agents {
				    if targeted_box = box_to_remove {
				        targeted_box <- nil;
				    }
				    if carried_box = box_to_remove {
				    	carried_box <- nil;
				    }
				}
	            
	            ask box_to_remove { do die; }

	            carried_box <- nil;
	            target_nest <- nil;
	        } 
	    }
    
    reflex die when: battery <= 0 {
        if (carried_box != nil) {
            carried_box.owner <- nil;
            carried_box <- nil;
        }
        if (targeted_box != nil) {
            targeted_box.owner <- nil;
            targeted_box <- nil;
        }    
        color <- rgb("black");
        // do die;		// dont kill robot from simulation as zombie robots prevent survivorship bias!
    }
    
    
    // ===== COMMON ASPECTS =====
    aspect default {        
        draw triangle(1) color: color;
        draw string("Robot") color: color size: 0.5;            
    }
    
    aspect icon {
        image_file robot_shape <- file('../images/robot.png');
        float cell_width <- world.shape.width / 50;
        float cell_height <- world.shape.height / 50;
        draw robot_shape size: {cell_width, cell_height} rotate: my heading + 1 wireframe: false; 
    }
}