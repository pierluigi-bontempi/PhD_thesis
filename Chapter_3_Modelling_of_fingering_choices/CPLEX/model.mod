//GUITAR FINGERING GENERATOR
using CPLEX;

////DATA STRUCTURES
////instrument features

int     f_max   = ...;
int 	s_max	= ...;
range   Frets  	= 1..f_max;
range   Strings  	= 1..s_max;

{string}	PlayableSounds = ...;

tuple combination {
  int corda;
  int fret;
}
{combination} AllCombinations = {<s,f> | s in Strings, f in Frets};

{int} OpenStrings[PlayableSounds] = ...;
{combination} Combinations[PlayableSounds] = ...;

//melody
int m = ...;
range   Notes  	= 1..m;
range   NotesButFirst  	= 2..m;
string note[Notes] = ...;
float  availableTime[Notes] = ...;

//hand and comfort
range Fingers = 1..4;
range FingersButFirst = 2..4;
range HandPosition = 1..f_max;
int SP_max[FingersButFirst] = ...;
int f_lb = ...;
int f_ub = ...;
range HandPositionLB = 1..f_lb;
range HandPositionUB = f_ub..f_max;
float timePerFret = ...;
float d_PC = ...;
float d_SC = ...;
float d_HS = ...;
float d_DH = ...;
float d_NO = ...;

//opt preferences
float alpha_PC = ...;
float alpha_SC = ...;
float alpha_HS = ...;
float alpha_DH = ...;
float alpha_NO = ...;


//CHECKS
execute{
	if (alpha_PC < 0 || alpha_SC < 0 || alpha_HS < 0 || alpha_DH < 0 || alpha_NO < 0){
		writeln("INPUT ERROR: Negative value of alpha weights in the obj function.");
	} 
	if (alpha_PC + alpha_SC + alpha_HS + alpha_DH + alpha_NO != 1){
		writeln("INPUT ERROR: Sum of alpha weights different from 1 in the obj function.");
	} 
}
assert (alpha_PC >= 0 && alpha_SC >= 0 && alpha_HS >= 0 && alpha_DH >= 0 && alpha_NO >= 0);
assert (alpha_PC + alpha_SC + alpha_HS + alpha_DH + alpha_NO == 1);



////VARIABLES---------------------------------
dvar boolean o[Notes][Strings];
dvar boolean y[Notes][HandPosition][Fingers][AllCombinations];
dvar boolean x[Notes][Frets];

//EXPR
dexpr float PC[i in NotesButFirst] = abs(
	sum(p in HandPosition) p * x[i-1][p] - sum(p in Frets) p * x[i][p]
	);
	
dexpr float SC[i in NotesButFirst] = abs(
	sum(p in HandPosition) sum(h in Fingers) sum(c in AllCombinations) c.corda * y[i-1][p][h][c]  - 
	sum(p in HandPosition) sum(h in Fingers) sum(c in AllCombinations) c.corda * y[i][p][h][c] +
	sum(s in OpenStrings[note[i-1]]) s * o[i-1][s] -
	sum(s in OpenStrings[note[i]]) s * o[i][s]
	);
	
dexpr float HS[i in Notes] = 
	sum(p in HandPosition) 
	sum(h in FingersButFirst) 
	sum(c in AllCombinations) (c.fret-p-h+1) * y[i][p][h][c];
	
dexpr float DH[i in Notes] = 
	 sum(p in HandPositionLB) (f_lb - p) * x[i][p] +
	 sum(p in HandPositionUB) (p - f_ub) * x[i][p];
	
dexpr float tot_PC = sum (i in NotesButFirst) PC[i];
dexpr float tot_SC = sum (i in NotesButFirst) SC[i];
dexpr float tot_HS = sum (i in Notes) HS[i] ;
dexpr float tot_DH = sum (i in Notes) DH[i];	 
dexpr float tot_NO = sum (i in Notes) sum(s in Strings : s in OpenStrings[note[i]]) o[i][s];
	 

////MODEL
minimize
  alpha_PC * d_PC * tot_PC
  + alpha_SC * d_SC * tot_SC 
  + alpha_HS * d_HS * tot_HS
  + alpha_DH * d_DH * tot_DH
  + alpha_NO * d_DH * tot_NO;
  
subject to {
    
forall(i in Notes)
   	vinc2:
  	sum(s in Strings : s in OpenStrings[note[i]]) o[i][s] +
	sum(p in HandPosition) sum(h in Fingers) sum(c in Combinations[note[i]]) y[i][p][h][c] 
	== 1;

forall(i in Notes)
   	vinc2neg:
	sum(p in HandPosition) sum(h in Fingers) sum(c in AllCombinations : c not in Combinations[note[i]]) y[i][p][h][c] 
	== 0;

forall(i in Notes)
   	vinc3:
	sum(p in HandPosition) x[i][p] == 1;
	
forall(i in Notes)
  forall(p in HandPosition)
  	vinc4:
   	sum(h in Fingers) sum(c in AllCombinations) y[i][p][h][c] <= x[i][p];

forall(i in NotesButFirst)
  forall(p in HandPosition)
  	vinc5:
   	x[i][p] - x[i-1][p] <= 1 - sum(s in OpenStrings[note[i]]) o[i][s];

forall(i in NotesButFirst)
   	vinc6:
	timePerFret * PC[i] <= availableTime[i];
	
forall(i in Notes)
  forall(p in HandPosition)
    forall(h in FingersButFirst)
      forall(c in AllCombinations)
   		vinc7:
	   	0 <= (c.fret-p-h+1) * y[i][p][h][c] <= SP_max[h];

forall(i in Notes)
  forall(p in HandPosition)
      forall(c in AllCombinations)
   		vinc9:
	   	(c.fret-p) * y[i][p][1][c] == 0;
	   	


//-- not the same finger, unless it is the same fret on different strings (barre') or it is on the same string
forall(i in NotesButFirst)
	forall(h in Fingers)
	  forall(c in AllCombinations)
   			vinc10c:
	   		sum(p in HandPosition) sum(c1 in AllCombinations : c1.fret != c.fret && c1.corda != c.corda) y[i][p][h][c1] 
	   		<= 1 - sum(p in HandPosition) y[i-1][p][h][c];


}//s.t.

execute {

// OUTPUT 1
writeln("Note\tString\tFret\tHandposition\tFinger");
for (i in Notes){
	
	//note
	write(note[i],"\t");

	//if open string
	for (s in Strings){
		if (o[i][s] == 1){
			write(s, "\t0\t");
		}
	}

	//combinations
	for(p in Frets){
		for(h in Fingers){
			for(c in AllCombinations){
				if (y[i][p][h][c] == 1){
					write(c.corda, "\t", c.fret, "\t");
				}
			}
		}
	}

	//fret finger combinations
	var found = 0;
	for(p in Frets){
		if (x[i][p] == 1){
			write(p, "\t");
			for(h in Fingers){
				for(c in AllCombinations){
					if (y[i][p][h][c] == 1){
						write(h, "\t");
						found = 1;
					}
				}
			}
		}
	}
	if (found == 0)
		write("x\t");

	write("\n");

} // for each i

write("\n");


// OUTPUT 2
for (i in Notes){
	// open strings
	for (s in Strings){
		if (o[i][s] == 1){
			write(s, ",");
		}
	}
	// combinations
	for(p in Frets){
		for(h in Fingers){
			for(c in AllCombinations){
				if (y[i][p][h][c] == 1){
					write(c.corda, ",");
				}
			}
		}
	}
}
write("\n");

// fret
for (i in Notes){

	var trovato = 0;
	// combinations
	for(p in Frets){
		for(h in Fingers){
			for(c in AllCombinations){
				if (y[i][p][h][c] == 1){
					write(c.fret, ",");
					trovato = 1;
				}
			}
		}
	}

	if (trovato == 0) write("0,");

} // for all i
write("\n");

// finger
for (i in Notes){

	var found = 0;
	for(p in Frets){
		for(h in Fingers){
			for(c in AllCombinations){
				if (y[i][p][h][c] == 1){
					write(h, ",");
					found = 1;
				}
			}
		}
	}
	if (found == 0)
		write("0,");

} 

}// forall i

