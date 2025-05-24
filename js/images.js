const petDiv = document.getElementById("other-page-pets");
const petImg = document.getElementById("animal");

petImg.style.display = "none";
petDiv.addEventListener("mouseover", showPet);
petDiv.addEventListener("mouseout", noPet);

function showPet(){
    petImg.setAttribute("style","display: box");
}
//display: none 

function noPet(){
    petImg.setAttribute("style","display: none ");
}

const cookingDiv = document.getElementById("other-page-cooking");
const cookingImg = document.getElementById("food");

cookingImg.style.display = "none";
cookingDiv.addEventListener("mouseover", showFood);
cookingDiv.addEventListener("mouseout", noFood);

function showFood(){
    cookingImg.setAttribute("style","display: box");
}

function noFood(){
    cookingImg.setAttribute("style","display: none ");
}

const travelDiv = document.getElementById("other-page-travel");
const travelImg = document.getElementById("travelvac");
travelImg.style.display = "none";
travelDiv.addEventListener("mouseover", showTravel);
travelDiv.addEventListener("mouseout", noTravel);

function showTravel(){
    travelImg.setAttribute("style","display: box");
}

function noTravel(){
    travelImg.setAttribute("style","display: none ");
}
