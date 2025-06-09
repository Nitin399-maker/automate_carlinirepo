document.addEventListener('DOMContentLoaded', function() {
    const testCaseSelect = document.getElementById('testCaseSelect');
    const testCaseContent = document.getElementById('testCaseContent');
    const processingFlow = document.getElementById('processingFlow');
    const evaluateBtn = document.getElementById('evaluateBtn');
    const generatedCode = document.getElementById('generatedCode');
    const copyBtn = document.getElementById('copyBtn');
    const loader = document.getElementById('loader');
    const yamlConfig = document.getElementById('yamlConfig');
    const copyYamlBtn = document.getElementById('copyYamlBtn');
    const apiKeyInput = document.getElementById('apiKeyInput');
    
    const generatedCodeCard = document.querySelector('#generatedCode').closest('.card');
    const yamlConfigCard = document.querySelector('#yamlConfig').closest('.card');
    
    generatedCodeCard.style.display = 'none';
    yamlConfigCard.style.display = 'none';
    
    let testCases = {};
    let classes = {};
    let currentTestCase = null;
    let currentFlow = null;

    function updateEvaluateButtonState() {
        evaluateBtn.disabled = !currentFlow || !apiKeyInput.value.trim();
    }
    
    apiKeyInput.addEventListener('input', updateEvaluateButtonState);
    
    fetch('test_cases.json').then(response => response.json()).then(data => {
            testCases = data;
            populateTestCaseDropdown(data);
        }).catch(error => {
            console.error('Error loading test cases:', error);
        });
    
    fetch('classes.json').then(response => response.json()).then(data => {
            classes = data;
        }).catch(error => {
            console.error('Error loading classes:', error);
        });
    
    function populateTestCaseDropdown(data) {
        for (const testName in data) {
            const option = document.createElement('option');
            option.value = testName;
            option.textContent = testName;
            testCaseSelect.appendChild(option);
        }
    }
    
    testCaseSelect.addEventListener('change', function() {
        const selectedTestCase = this.value;
        if (selectedTestCase) {
            currentTestCase = testCases[selectedTestCase];
            testCaseContent.innerHTML = '';
            testCaseContent.appendChild(
                formatCode(currentTestCase, 'python')
            );
            const flowMatch = currentTestCase.match(/Test\w+\s*=\s*([\s\S]*?)(?=\s*Test\w+\s*=|\s*if\s+__name__|\s*$)/);
            console.log('Flow match:', flowMatch);
            if (flowMatch && flowMatch[1]) {
                currentFlow = flowMatch[1];
                processingFlow.innerHTML = '';
                processingFlow.appendChild(
                    formatCode(currentFlow, 'python')
                );
                updateEvaluateButtonState();
            } else {
                processingFlow.innerHTML = '';
                processingFlow.appendChild(
                    formatCode('Processing flow not found', 'plaintext')
                );
                evaluateBtn.disabled = true;
            }
        } else {
            testCaseContent.innerHTML = '';
            processingFlow.innerHTML = '';
            evaluateBtn.disabled = true;
        }
        
        // Hide the cards again when changing test case
        generatedCodeCard.style.display = 'none';
        yamlConfigCard.style.display = 'none';
        
        generatedCode.innerHTML = '';
        copyBtn.disabled = true;
        yamlConfig.innerHTML = '';
        copyYamlBtn.disabled = true;
    });
    
    // Modify the evaluate button handler to use the API key from input
    evaluateBtn.addEventListener('click', async function(e) {
        if (!currentTestCase || !currentFlow) return;
        
        const apiKey = apiKeyInput.value.trim();
        if (!apiKey) {
            alert('Please enter your OpenRouter API key');
            return;
        }
        
        try {
            // First show the loader
            loader.classList.remove('d-none');
            
            // Hide both cards while processing
            generatedCodeCard.style.display = 'none';
            yamlConfigCard.style.display = 'none';
            
            generatedCode.innerHTML = '';
            const evaluationMatch = currentTestCase.match(/evaluation\s*=\s*"""([\s\S]*?)"""/);
            const evaluation = evaluationMatch ? evaluationMatch[1].trim() : 'You are the best at converting DSL to Promptfoo Python assertions.';
            const classNames = extractClassNames(currentFlow);
            const classImplementations = classNames.map(name => classes[name] || ``);
            const prompt = generatePrompt(currentTestCase, currentFlow, classImplementations);
            const result = await callLLMAPI(prompt, evaluation, apiKey); // Pass the API key
            const extractedCode = extractPythonCode(result);
            generatedCode.innerHTML = '';
            generatedCode.appendChild(
                formatCode(extractedCode, 'python')
            );
            copyBtn.disabled = false;
            
            // Generate YAML configuration
            const yamlConfiguration = generateYAMLConfig(currentTestCase, extractedCode);
            yamlConfig.innerHTML = '';
            yamlConfig.appendChild(
                formatCode(yamlConfiguration, 'yaml')
            );
            copyYamlBtn.disabled = false;
            
            // Show both cards after content is ready
            generatedCodeCard.style.display = 'block';
            yamlConfigCard.style.display = 'block';
            
        } catch (error) {
            console.error('Evaluation error:', error);
            generatedCode.innerHTML = '';
            generatedCode.appendChild(
                formatCode(`Error: ${error.message}`, 'plaintext')
            );
            
            // Show only the generated code card in case of error
            generatedCodeCard.style.display = 'block';
            
        } finally {
            // Hide loader
            loader.classList.add('d-none');
        }
    });

    function extractClassNames(flow) {
        const classRegex = /\b(\w+)\s*\(.*?\)/g;
        const matches = [];
        let match;
        while ((match = classRegex.exec(flow)) !== null) {
            matches.push(match[1]);
        }
        return matches;
    }

    function generatePrompt(testCase, flow, classImplementations) {
        return `${testCase}

I have an evaluation process using a custom DSL,whose custome DSL is given above but I want to convert it to use Promptfoo. The evaluation should start after the LLMRun step (the LLM response is already available via the Promptfoo YAML).
Write a simple Python assertion script compatible with Promptfoo. It must define a single function that takes response and context=None, uses subprocess (not Docker), and evaluates the response based on the ${flow} process. Keep it procedural—no classes, and no unnecessary complexity. Use the original DSL code only as a reference, but do not include or replicate its structure. Output only the final Python assertion file.

${classImplementations.join('\n\n')}`;
    }
    async function callLLMAPI(prompt,systemprompt,apiKey) {
        try {
            console.log(apiKey);
            const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
                method: 'POST',
                headers: {
                    "Content-Type": "application/json", 
                    Authorization: `Bearer ${apiKey}`
                },
                body: JSON.stringify({
                    model: "anthropic/claude-sonnet-4",
                    messages: [{role: "system",content: systemprompt},{role: "user",content: prompt}]
                })
            });
            const data = await response.json();
            if (data.error) {
                throw new Error(data.error.message);
            }
        
            return data.choices[0].message.content;
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }

    function formatCode(code, language) {
            code = code.trim();
            const pre = document.createElement('pre');
            const codeElement = document.createElement('code');
            codeElement.className = `language-${language}`;
            codeElement.textContent = code;
            pre.appendChild(codeElement);
            Prism.highlightElement(codeElement);
            return pre;
        }


    function extractPythonCode(response) {
    const codeBlockMatch = response.match(/```(?:python)?\n([\s\S]*?)\n```/);
    if (codeBlockMatch) {
        return codeBlockMatch[1].trim();
    }
    const pythonPatternMatch = response.match(/(?:import\s+|class\s+|def\s+|if\s+__name__\s*==\s*['"]__main__['"]:)([\s\S]*)/);
    if (pythonPatternMatch) {
        return pythonPatternMatch[0].trim();
    }
    return response.trim();
    }


    function generateYAMLConfig(testCase, pythonCode) {
        const descriptionMatch = testCase.match(/DESCRIPTION\s*=\s*"(.+?)"/);
        const description = descriptionMatch ? descriptionMatch[1] : 'Test case evaluation';
        const function_name = pythonCode.match(/def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*,\s*context\s*=\s*None\s*\)/);
        console.log('Function name match:', function_name);
        const questionMatch = testCase.match(/question\w*\s*=\s*"""([\s\S]*?)"""/);
        const question = questionMatch ? questionMatch[1].trim() : 'No question found';
        return `
description: "${description}"
providers:
- {id: openrouter:anthropic/claude-3.7-sonnet, config: { max_tokens: 8192 }}

defaultTest:
  assert: []
  vars: {}

tests:
 - description: "${description}"
   vars:
     prompt: |-
       ${question}
   assert:
     - type: python
       value: "file://${testCaseSelect.value}:${function_name[1]}"

# Persist for the web viewer
writeLatestResults: true
# Ensure caching stays on
commandLineOptions:
  cache: true
`;

    }

copyBtn.addEventListener('click', function(e) {
    const codeText = generatedCode.querySelector('code').textContent;
    const fileName = `${testCaseSelect.value}.py`;
    downloadFile(codeText, fileName, 'text/plain');
});

copyYamlBtn.addEventListener('click', function(e) {
    const yamlText = yamlConfig.querySelector('code').textContent;
    downloadFile(yamlText, 'promptfooconfig.yaml', 'text/plain');
});

function downloadFile(content, fileName, contentType) {
    const blob = new Blob([content], { type: contentType });
    const url = URL.createObjectURL(blob);
    const downloadLink = document.createElement('a');
    downloadLink.href = url;
    downloadLink.download = fileName;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
    URL.revokeObjectURL(url);
}
});