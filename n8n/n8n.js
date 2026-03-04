// Get the data from the Gateway
const intent = $input.first().json.body.intent;
const contract = $input.first().json.body.contract;
const context = $input.first().json.body.context;

const results = {
    authorized: true,
    reason: "Contract satisfied",
    resolved_constraints: {}
};

// Safety check: ensure objects exist
if (!intent || !contract || !context) {
  return { 
    authorized: false, 
    reason: "Critical Error: Engine received incomplete evaluation bundle." 
  };
}

// Evaluate Constraints
for (const [key, expression] of Object.entries(contract.constraints)) {
    try {
        const resolver = new Function("intent", "context", `return ${expression};`);
        results.resolved_constraints[key] = resolver(intent, context);
    } catch (e) {
        results.resolved_constraints[key] = `Error evaluating constraint: ${e}`;
    }
  }

// Apply Rules based on Resolved Constraints
for (const policy of contract.policies) {
    const validator = new Function("constraints", `return ${policy.condition};`);
    const is_valid = validator(results.resolved_constraints);

    if (!is_valid) {
        results.authorized = false;
        results.reason = policy.message;
        return results;
    }
}

return results;
