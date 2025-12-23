// A solution to Sol Levitt's Wall Drawing #11 (1969)
// "A wall divided horizontally and vertically into four equal parts.
// Within each part, three of the four kinds of lines are superimposed."
// The four kinds of lines will be horizontal, vertical, and both diagonals.
// Michael Seay, January 2022

let lineSpacing;

let horizontalPhase;
let verticalPhase;
let diagonalPhase1;
let diagonalPhase2;

let horizontalSpeed;
let verticalSpeed;
let diagonalSpeed1;
let diagonalSpeed2;

let quadrantMap;
let commonOffset;
let quadrantOffsetMap;

function setup() {
	createCanvas(displayHeight * 0.5, displayHeight * 0.5);
	background(255);
	strokeWeight(1);
	
	// Define the spacing between the lines
	lineSpacing = displayHeight * 0.05;  // 80;  200;
	
	horizontalPhase = 0; // 20;  100;
	verticalPhase = 0; // 40;  100;
	diagonalPhase1 = 0; // -20;  100;
	diagonalPhase2 = 0;  // 0; 100;
	
	horizontalSpeed = 1.25; // 1.25;
	verticalSpeed = 1; // 1;
	diagonalSpeed1 = 0.75; // 0.75;
	diagonalSpeed2 = 0.5; // 0.5;
	
		// Define the top left point of each quadrant
	quadrantMap = {0: [width / 2, 0],
								 1: [0, 0],
								 3: [0, height / 2],
								 2: [width / 2, height / 2]};
	
	// Define an additional independent offset for each quadrant
	commonOffset = 0;
	quadrantOffsetMap = {0: [commonOffset, -commonOffset],
											 1: [-commonOffset, -commonOffset],
											 3: [-commonOffset, commonOffset],
											 2: [commonOffset, commonOffset]};
}

function draw() {
	
	clear()

	// Draw the quadrants
	line(width / 2, 0, width / 2, height);
	line(0, height / 2, width, height / 2);
	
	horizontalPhase = (horizontalPhase + horizontalSpeed) % lineSpacing;
	verticalPhase = (verticalPhase + verticalSpeed) % lineSpacing;
	diagonalPhase1 = (diagonalPhase1 + diagonalSpeed1) % lineSpacing;
	diagonalPhase2 = (diagonalPhase2 + diagonalSpeed2) % lineSpacing;

	// For each quadrant, we will render all four line types
	for (let quadrantInd = 0; quadrantInd < 4; quadrantInd += 1) {
		
		let quadrantX = quadrantMap[quadrantInd][0] + quadrantOffsetMap[quadrantInd][0]
		let quadrantY = quadrantMap[quadrantInd][1] + quadrantOffsetMap[quadrantInd][1]
		
		// For each line type, check if it's to be skipped
		for (let lineInd = 0; lineInd < 4; lineInd += 1) {
			
			if (quadrantInd === lineInd) {
				continue
			}
			
			// Render the lines within the quadrant based on type
			if (lineInd === 0) {
				let yS = quadrantY + horizontalPhase;
				let yE = quadrantY + height / 2 - 1;
				for (yC = yS; yC <= yE; yC += lineSpacing) {
					line(quadrantX, yC, quadrantX + width / 2, yC)
				}
			} else if (lineInd === 2) {
				let xS = quadrantX + verticalPhase;
				let xE = quadrantX + width / 2 - 1;
				for (xC = xS; xC <= xE; xC += lineSpacing) {
					line(xC, quadrantY, xC, quadrantY + height / 2)
				}
			} else if (lineInd === 1) {
				let dS2 = diagonalPhase1;
				let dE2 = diagonalPhase1 + width / 2 - 1;
				for (dC1 = dS2; dC1 <= dE2; dC1 += lineSpacing) {
					line(quadrantX, quadrantY + height / 2 - dC1,
							 quadrantX + dC1, quadrantY + height / 2)
					line(quadrantX + dC1, quadrantY,
							 quadrantX + width / 2, quadrantY + height / 2 - dC1)
				}
			} else if (lineInd === 3) {
				let dS3 = diagonalPhase2;
				let dE3 = diagonalPhase2 + height / 2 - 1;
				for (dC2 = dS3; dC2 <= dE3; dC2 += lineSpacing) {
					line(quadrantX + dC2, quadrantY + height / 2,
							 quadrantX + width / 2, quadrantY + dC2)
					line(quadrantX, quadrantY + dC2,
							 quadrantX + dC2, quadrantY)
				}
			}
		}
	}
}
