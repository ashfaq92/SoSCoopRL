/**
* Name: robotsaphesia
* Based on the internal empty template. 
* Author: ashfa
* Tags: 
*/


model robot_saphesia

import "robot_cooperative.gaml"

global {
	 // SApHESIA Model Parameters (from research paper)
    float BATTERY_DYING_THRESHOLD <- 1.0/3.0;        // robot.battery < MaxNe/3
    float CRITICALITY_THRESHOLD_NEEDS_HELP <- 0.3;   // RDying > Rr/2  
    // Paper doesn't specify "can help" threshold, so we'll use a reasonable value
    float CRITICALITY_THRESHOLD_CAN_HELP <- 0.7;     // System can help if < 60% dying
    
    // FIPA Message Constants
    string MSG_HELP_REQUEST <- "help_request";
    string MSG_HELP_ACCEPTED <- "help_accepted"; 
    string MSG_HELP_REFUSED <- "help_refused";
}


species component_system skills: [fipa] {
	rgb system_color;
    list<robot_cooperative > robots update: robot_cooperative where (each.color = system_color and !dead(each));
    list<robot_cooperative> dying_robots update: robots where (each.battery < each.max_battery * BATTERY_DYING_THRESHOLD);
    

    
    list <component_system> linked_systems;
    
    // saphesia model attributes
    int component_criticality update: length(dying_robots);
    float criticality_ratio update: (length(robots) = 0) ? 0.0 : (length(dying_robots) / length(robots));
    bool needs_help update: criticality_ratio > CRITICALITY_THRESHOLD_NEEDS_HELP; // more than half robots dying
    bool is_helping <- false;
    
    init {
    	linked_systems <- component_system - self;  //populate each component system's list of all OTHER component systems (excluding itself).
    } 
    
 
  
    
    
    
    // Basic help actions
    action help_system(component_system target_system) {
        write "Component " + system_color + " helping " + target_system.system_color;
        ask robots {
        	helped_colors <- helped_colors + target_system.system_color;
	        write self.name + " now values " + target_system.system_color + " boxes highly";
        }
        is_helping <- true;
    }

    action stop_helping(component_system target_system) {
        write "Component " + system_color + " stopping help to " + target_system.system_color;
        ask robots {
        	helped_colors <- helped_colors - target_system.system_color;	
        }
        is_helping <- false;
    }

	
	// request help when in critical state
    reflex request_help when: needs_help and !is_helping {
    	write "System:" + system_color + ' requesting help ' + length(dying_robots);
    	
    	loop target_system over: linked_systems {
    		if !target_system.is_helping and target_system.criticality_ratio < CRITICALITY_THRESHOLD_CAN_HELP {
		    	do start_conversation to: [target_system] protocol: 'fipa-request' performative: 'request' contents: [MSG_HELP_REQUEST, system_color];
    			
    		}
    	}
    }
    
    // process incoming help requests
    reflex process_requests when: !empty(requests) {
    	loop request over: requests {
    		string req_content <- request.contents[0];
    		if req_content = MSG_HELP_REQUEST {
    			rgb requester_color <- rgb(request.contents[1]);
                component_system requester <- first(linked_systems where (each.system_color = requester_color));
    			
    			if requester != nil and criticality_ratio < CRITICALITY_THRESHOLD_CAN_HELP {
					do agree message: request contents: [MSG_HELP_ACCEPTED];					
					do help_system(requester);
                    write "System " + system_color + " agreed to help " + requester_color;
    			} else {
    				do refuse message: request contents: [MSG_HELP_REFUSED];
                    write "System " + system_color + " refused to help " + requester_color;
    			}
    			
    		}
    	}
    	
    } 
    
    
    reflex log {
    	write("System:" + system_color + " Robots:" + length(robots) + " Dying:" + length(dying_robots));
    }
    
    

    
    aspect default {
		    // Simple circle without complex positioning
		    draw circle(2) color: system_color border: rgb("black") width: 1;
		    
		    // Simple text without newlines, using contrasting color
		    draw string("Sys:" + system_color + " R:" + length(robots) + " D:" + length(dying_robots)) 
		        color: rgb("black") size: 0.8;
		}
}
