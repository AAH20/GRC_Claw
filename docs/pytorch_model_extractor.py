import torch
import torch.nn as nn
import re
from collections import OrderedDict

def analyze_model_architecture(model_path):
    """Analyze any PyTorch model architecture from saved file"""
    checkpoint = torch.load(model_path, map_location='cpu')
    
    # Extract state_dict
    if isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
        state_dict = checkpoint['state_dict']
    elif isinstance(checkpoint, dict):
        state_dict = checkpoint
    else:
        try:
            state_dict = checkpoint.state_dict()
        except:
            print("Could not extract state_dict")
            return None
            
    # Print all layers with their shapes
    print("Model state_dict contents:")
    for key, tensor in state_dict.items():
        print(f"{key}: {tensor.shape}")
    
    return state_dict

def infer_model_architecture(state_dict):
    """Infer model architecture from state_dict"""
    # Remove module prefix if exists
    clean_dict = OrderedDict()
    for key, value in state_dict.items():
        clean_key = re.sub(r'^module\.', '', key)
        clean_dict[clean_key] = value
    
    # Create hierarchy of layers
    layers = {}
    layer_order = []
    
    for key, tensor in clean_dict.items():
        parts = key.split('.')
        
        if len(parts) >= 2:
            # Extract layer name and parameter type
            param_type = parts[-1]
            layer_name = '.'.join(parts[:-1])
            
            if layer_name not in layers:
                layers[layer_name] = {'params': {}}
                layer_order.append(layer_name)
            
            layers[layer_name]['params'][param_type] = tensor.shape
            
            # Determine layer type
            if 'gru' in layer_name.lower() and ('weight_ih' in param_type or 'weight_hh' in param_type):
                layers[layer_name]['type'] = 'gru'
            elif 'lstm' in layer_name.lower() and ('weight_ih' in param_type or 'weight_hh' in param_type):
                layers[layer_name]['type'] = 'lstm'
            elif 'conv' in layer_name.lower() and 'weight' in param_type:
                layers[layer_name]['type'] = 'conv'
            elif ('linear' in layer_name.lower() or 'fc' in layer_name.lower() or 'dense' in layer_name.lower()) and 'weight' in param_type:
                layers[layer_name]['type'] = 'linear'
            elif 'embedding' in layer_name.lower():
                layers[layer_name]['type'] = 'embedding'
            elif 'batch' in layer_name.lower() and 'norm' in layer_name.lower():
                layers[layer_name]['type'] = 'batchnorm'
            elif 'layer' in layer_name.lower() and 'norm' in layer_name.lower():
                layers[layer_name]['type'] = 'layernorm'
    
    # Infer the sequence of operations
    model_sequence = []
    for layer_name in layer_order:
        layer_info = layers[layer_name]
        
        if layer_info.get('type') == 'linear':
            in_features = layer_info['params']['weight'][1]
            out_features = layer_info['params']['weight'][0]
            model_sequence.append({
                'name': layer_name,
                'type': 'linear',
                'in_features': in_features,
                'out_features': out_features
            })
            
            # Infer potential activation after linear layers
            if layer_name != layer_order[-1]:  # Not the last layer
                model_sequence.append({
                    'name': f"{layer_name}_activation",
                    'type': 'activation',
                    'activation_type': 'relu'  # Default assumption
                })
        
        elif layer_info.get('type') == 'gru':
            # For GRU: input_size from weight_ih_l0, hidden_size from weight_ih_l0 / 3
            if 'weight_ih_l0' in layer_info['params']:
                hidden_size = layer_info['params']['weight_ih_l0'][0] // 3
                input_size = layer_info['params']['weight_ih_l0'][1]
                
                # Count number of layers
                layer_nums = set()
                for param_name in layer_info['params']:
                    if param_name.startswith('weight_ih_l'):
                        layer_num = int(param_name.split('_l')[1].split('.')[0])
                        layer_nums.add(layer_num)
                num_layers = max(layer_nums) + 1 if layer_nums else 1
                
                # Check if bidirectional
                bidirectional = any('reverse' in param for param in layer_info['params'])
                
                model_sequence.append({
                    'name': layer_name,
                    'type': 'gru',
                    'input_size': input_size,
                    'hidden_size': hidden_size,
                    'num_layers': num_layers,
                    'bidirectional': bidirectional
                })
        
        elif layer_info.get('type') == 'lstm':
            # For LSTM: input_size from weight_ih_l0, hidden_size from weight_ih_l0 / 4
            if 'weight_ih_l0' in layer_info['params']:
                hidden_size = layer_info['params']['weight_ih_l0'][0] // 4
                input_size = layer_info['params']['weight_ih_l0'][1]
                
                # Count number of layers
                layer_nums = set()
                for param_name in layer_info['params']:
                    if param_name.startswith('weight_ih_l'):
                        layer_num = int(param_name.split('_l')[1].split('.')[0])
                        layer_nums.add(layer_num)
                num_layers = max(layer_nums) + 1 if layer_nums else 1
                
                # Check if bidirectional
                bidirectional = any('reverse' in param for param in layer_info['params'])
                
                model_sequence.append({
                    'name': layer_name,
                    'type': 'lstm',
                    'input_size': input_size,
                    'hidden_size': hidden_size,
                    'num_layers': num_layers,
                    'bidirectional': bidirectional
                })
        
        elif layer_info.get('type') == 'conv':
            # Handle different conv dimensions
            weight_shape = layer_info['params']['weight']
            if len(weight_shape) == 4:  # Conv2d
                out_channels, in_channels = weight_shape[0], weight_shape[1]
                kernel_size = (weight_shape[2], weight_shape[3])
                model_sequence.append({
                    'name': layer_name,
                    'type': 'conv2d',
                    'in_channels': in_channels,
                    'out_channels': out_channels,
                    'kernel_size': kernel_size
                })
            elif len(weight_shape) == 3:  # Conv1d
                out_channels, in_channels = weight_shape[0], weight_shape[1]
                kernel_size = weight_shape[2]
                model_sequence.append({
                    'name': layer_name,
                    'type': 'conv1d',
                    'in_channels': in_channels,
                    'out_channels': out_channels,
                    'kernel_size': kernel_size
                })
            
            # Add potential BatchNorm and activation after convolution
            model_sequence.append({
                'name': f"{layer_name}_activation",
                'type': 'activation',
                'activation_type': 'relu'  # Default assumption
            })
            
        elif layer_info.get('type') == 'batchnorm':
            # Determine the dimension from the running_mean shape
            if 'running_mean' in layer_info['params']:
                num_features = layer_info['params']['running_mean'][0]
                model_sequence.append({
                    'name': layer_name,
                    'type': 'batchnorm',
                    'num_features': num_features
                })
                
        elif layer_info.get('type') == 'embedding':
            if 'weight' in layer_info['params']:
                num_embeddings, embedding_dim = layer_info['params']['weight']
                model_sequence.append({
                    'name': layer_name,
                    'type': 'embedding',
                    'num_embeddings': num_embeddings,
                    'embedding_dim': embedding_dim
                })
    
    return model_sequence

def generate_model_code(model_sequence):
    """Generate PyTorch model code based on the inferred architecture"""
    imports = [
        "import torch",
        "import torch.nn as nn",
        "import torch.nn.functional as F",
        ""
    ]
    
    class_def = [
        "class ReconstructedModel(nn.Module):",
        "    def __init__(self):",
        "        super(ReconstructedModel, self).__init__()"
    ]
    
    init_code = []
    forward_code = ["    def forward(self, x):"]
    
    # Special handling for RNN outputs
    has_rnn = any(layer['type'] in ['lstm', 'gru'] for layer in model_sequence)
    rnn_output_processed = False
    
    for i, layer in enumerate(model_sequence):
        layer_type = layer['type']
        layer_name = layer['name'].replace('.', '_')
        
        if layer_type == 'linear':
            init_code.append(f"        self.{layer_name} = nn.Linear({layer['in_features']}, {layer['out_features']})")
            forward_code.append(f"        x = self.{layer_name}(x)")
            
        elif layer_type == 'activation':
            if layer['activation_type'].lower() == 'relu':
                forward_code.append(f"        x = F.relu(x)")
            elif layer['activation_type'].lower() == 'sigmoid':
                forward_code.append(f"        x = torch.sigmoid(x)")
            elif layer['activation_type'].lower() == 'tanh':
                forward_code.append(f"        x = torch.tanh(x)")
            
        elif layer_type == 'gru':
            init_code.append(f"        self.{layer_name} = nn.GRU(")
            init_code.append(f"            input_size={layer['input_size']},")
            init_code.append(f"            hidden_size={layer['hidden_size']},")
            init_code.append(f"            num_layers={layer['num_layers']},")
            init_code.append(f"            batch_first=True,")
            init_code.append(f"            bidirectional={layer['bidirectional']}")
            init_code.append(f"        )")
            
            forward_code.append(f"        output, hidden = self.{layer_name}(x)")
            
            # Check if this is followed by a linear layer directly
            if i + 1 < len(model_sequence) and model_sequence[i+1]['type'] == 'linear':
                if layer['bidirectional']:
                    forward_code.append(f"        x = output[:, -1, :]  # Last time step")
                else:
                    forward_code.append(f"        x = output[:, -1, :]  # Last time step")
                rnn_output_processed = True
            else:
                forward_code.append(f"        x = output")
            
        elif layer_type == 'lstm':
            init_code.append(f"        self.{layer_name} = nn.LSTM(")
            init_code.append(f"            input_size={layer['input_size']},")
            init_code.append(f"            hidden_size={layer['hidden_size']},")
            init_code.append(f"            num_layers={layer['num_layers']},")
            init_code.append(f"            batch_first=True,")
            init_code.append(f"            bidirectional={layer['bidirectional']}")
            init_code.append(f"        )")
            
            forward_code.append(f"        output, (hidden, cell) = self.{layer_name}(x)")
            
            # Check if this is followed by a linear layer directly
            if i + 1 < len(model_sequence) and model_sequence[i+1]['type'] == 'linear':
                if layer['bidirectional']:
                    forward_code.append(f"        x = output[:, -1, :]  # Last time step")
                else:
                    forward_code.append(f"        x = output[:, -1, :]  # Last time step")
                rnn_output_processed = True
            else:
                forward_code.append(f"        x = output")
            
        elif layer_type == 'conv1d':
            init_code.append(f"        self.{layer_name} = nn.Conv1d(")
            init_code.append(f"            in_channels={layer['in_channels']},")
            init_code.append(f"            out_channels={layer['out_channels']},")
            init_code.append(f"            kernel_size={layer['kernel_size']}")
            init_code.append(f"        )")
            forward_code.append(f"        x = self.{layer_name}(x)")
            
        elif layer_type == 'conv2d':
            init_code.append(f"        self.{layer_name} = nn.Conv2d(")
            init_code.append(f"            in_channels={layer['in_channels']},")
            init_code.append(f"            out_channels={layer['out_channels']},")
            init_code.append(f"            kernel_size={layer['kernel_size']}")
            init_code.append(f"        )")
            forward_code.append(f"        x = self.{layer_name}(x)")
            
        elif layer_type == 'batchnorm':
            init_code.append(f"        self.{layer_name} = nn.BatchNorm1d({layer['num_features']})")
            forward_code.append(f"        x = self.{layer_name}(x)")
            
        elif layer_type == 'embedding':
            init_code.append(f"        self.{layer_name} = nn.Embedding({layer['num_embeddings']}, {layer['embedding_dim']})")
            forward_code.append(f"        x = self.{layer_name}(x)")
    
    # Add special handling if there's an RNN but its output wasn't explicitly processed
    if has_rnn and not rnn_output_processed:
        # Add a comment to indicate modification might be needed
        forward_code.append("        # Note: You may need to reshape RNN output depending on your use case")
        forward_code.append("        # For classification, typically: x = x[:, -1, :]  # Get last time step")
    
    forward_code.append("        return x")
    
    # Combine all code parts
    full_code = imports + [""] + class_def + init_code + [""] + forward_code
    
    return "\n".join(full_code)

def extract_model_from_checkpoint(model_path):
    """Main function to extract model architecture from checkpoint and generate code"""
    state_dict = analyze_model_architecture(model_path)
    if state_dict is None:
        return "Failed to analyze model architecture"
    
    print("\nInferring model architecture...")
    model_sequence = infer_model_architecture(state_dict)
    
    print("\nInferred model structure:")
    for layer in model_sequence:
        print(f"- {layer['name']} ({layer['type']})")
    
    print("\nGenerating model code...")
    model_code = generate_model_code(model_sequence)
    
    print("\nGenerated model code:")
    print(model_code)
    
    return model_code

# Usage example:
# model_code = extract_model_from_checkpoint('path/to/model.pt')
# 
# # Save the generated code to a file
# with open('reconstructed_model.py', 'w') as f:
#     f.write(model_code)
#
# # To load the model with the original weights:
# from reconstructed_model import ReconstructedModel
# model = ReconstructedModel()
# checkpoint = torch.load('path/to/model.pt', map_location='cpu')
# if isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
#     model.load_state_dict(checkpoint['state_dict'])
# else:
#     model.load_state_dict(checkpoint)