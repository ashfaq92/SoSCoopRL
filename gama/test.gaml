model main
import "cell_.gaml"
import "nest.gaml"
import "box_.gaml"
//import "robot_random.gaml"
//import "robot_greedy.gaml"
//import "robot_cooperative.gaml"
import "robot_double_cooperative.gaml"

global {
	list<rgb> colors <- [rgb("red"), rgb("green"), rgb("blue")];
	
    string robot_type_param <- "double_cooperative";
    
    
    action spawn_nests { 
        create nest with: [ color:rgb("red"), location:cell[15,15].location ];
        create nest with: [ color:rgb("green"), location:cell[35,15].location ];
        create nest with: [ color:rgb("blue"), location:cell[25,32].location ];
    }
    
    action create_robots_with_colors(string robot_type) {
        create robot_double_cooperative number: 200 with: [color::one_of(colors)];
    }
    

    
}


experiment myExperiment type:gui {
	
	init {
        create simulation with: [seed::seed];
        ask simulation {
            do spawn_nests();
            create box_ number: 90;
            do create_robots_with_colors(robot_type_param);
        }
    }
	output {
		display myDisplay type:opengl {
			grid cell border: #black;
			species cell aspect:default;
			species nest aspect:default;
			species box_ aspect:default;
			species robot_double_cooperative aspect:default;
		}
	}
}

