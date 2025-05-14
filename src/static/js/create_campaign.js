let currentStep = 1;
const steps = document.querySelectorAll(".campaign-step");

function showStep(stepNumber) {
    steps.forEach(step => step.classList.remove("active-step"));
    document.getElementById(`step${stepNumber}`).classList.add("active-step");
    currentStep = stepNumber;
    if (stepNumber === 4) {
        updateCampaignSummary();
    }
    if (stepNumber === 3) {
        fetchChannelSuggestions();
    }
}

function nextStep() {
    if (currentStep < steps.length) {
        // Basic validation for current step before proceeding (can be expanded)
        let valid = true;
        const currentStepInputs = steps[currentStep - 1].querySelectorAll("input[required], select[required], textarea[required]");
        currentStepInputs.forEach(input => {
            if (!input.value) {
                valid = false;
                input.style.borderColor = "red"; // Highlight empty required fields
            } else {
                input.style.borderColor = "#ccc";
            }
        });

        if (!valid) {
            alert("Please fill in all required fields for the current step.");
            return;
        }
        showStep(currentStep + 1);
    }
}

function prevStep() {
    if (currentStep > 1) {
        showStep(currentStep - 1);
    }
}

function updateCampaignSummary() {
    document.getElementById("summaryCampaignName").textContent = document.getElementById("campaignName").value;
    document.getElementById("summaryMarketingGoal").textContent = document.getElementById("marketingGoal").selectedOptions[0].text;
    document.getElementById("summaryTotalBudget").textContent = document.getElementById("totalBudget").value;
    document.getElementById("summaryStartDate").textContent = document.getElementById("startDate").value;
    document.getElementById("summaryEndDate").textContent = document.getElementById("endDate").value;
    document.getElementById("summaryLocation").textContent = document.getElementById("location").value;
    document.getElementById("summaryRadius").textContent = document.getElementById("radius").value;
    document.getElementById("summaryInterests").textContent = document.getElementById("interests").value;
    document.getElementById("summaryAdHeadline").textContent = document.getElementById("adHeadline").value;

    const selectedChannels = [];
    document.querySelectorAll("#suggestedChannels input[type=\"checkbox\"]:checked").forEach(checkbox => {
        selectedChannels.push(checkbox.value);
    });
    document.getElementById("summaryChannels").textContent = selectedChannels.join(", ") || "None selected";
}

async function fetchChannelSuggestions() {
    const budget = document.getElementById("totalBudget").value;
    const interests = document.getElementById("interests").value;
    const location = document.getElementById("location").value;
    const suggestedChannelsDiv = document.getElementById("suggestedChannels");
    suggestedChannelsDiv.innerHTML = "<p>Fetching AI-powered channel suggestions...</p>";

    try {
        const response = await fetch("/api/suggest-channels", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ 
                budget: budget,
                target_audience_description: interests, // Simplified for prototype
                smb_location: location // Added location for context
            }),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        if (data.suggestions && data.suggestions.length > 0) {
            let channelsHTML = "<ul>";
            data.suggestions.forEach(channel => {
                channelsHTML += `<li><input type="checkbox" name="selected_channels" value="${channel.name}" id="channel_${channel.id}"> <label for="channel_${channel.id}">${channel.name} (Relevance: ${channel.relevance_score.toFixed(2)}) - ${channel.reason}</label></li>`;
            });
            channelsHTML += "</ul>";
            suggestedChannelsDiv.innerHTML = channelsHTML;
        } else if (data.message) {
             suggestedChannelsDiv.innerHTML = `<p>${data.message}</p>`;
        } else {
            suggestedChannelsDiv.innerHTML = "<p>No channel suggestions available at the moment. Please proceed with manual selection or try refining your inputs.</p>";
        }
    } catch (error) {
        console.error("Error fetching channel suggestions:", error);
        suggestedChannelsDiv.innerHTML = "<p>Could not load channel suggestions. Please try again later or proceed manually.</p>";
    }
}

// Initialize the first step
document.addEventListener("DOMContentLoaded", () => {
    showStep(1);
    // Add event listener for form submission if needed for AJAX, otherwise HTML form action will handle it
    const form = document.getElementById("createCampaignForm");
    form.addEventListener("submit", function(event) {
        // Final validation before submission
        if (currentStep !== 4) {
            event.preventDefault(); // Prevent submission if not on the review step
            alert("Please complete all steps before submitting.");
            return;
        }
        // Add any final client-side validation for step 4 if needed
        console.log("Form submitted");
    });
});

// Basic script for dashboard (if any dynamic content is needed later)
document.addEventListener("DOMContentLoaded", () => {
    // Placeholder for any dashboard specific JS
    console.log("Dashboard loaded");
});
