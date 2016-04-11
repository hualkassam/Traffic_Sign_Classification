__author__ = 'Hussam_Qassim'
'''
    Open text file for writing
   
	Read the images
	Resize the images
	Split them into train, valid, and test
		Reshape them
		Convert the type to suitable data type
	Build the model 2 layers CNN
	Build mini-batch iterator
	Train the model
	Test the model
	Extract features from hidden layers
	Feed the features to Random Forest
	Test it
	Check Accuracy
'''
import warnings # https://docs.python.org/2/library/warnings.html
warnings.filterwarnings("ignore")

from utilities import *
from neuralnet import *
import cPickle as pickle # https://docs.python.org/2/library/pickle.html#data-stream-format



totalTime = time()

text_file = open(root+"/statistics.txt", "w")
text_file.write("\n")

t = time()


images, targets= load_images()
x_train, y_train, x_valid, y_valid, x_test, y_test = split_data(images, targets)
network = build_model() # Call the build_model in th neuralnet file

learning_rate = 0.01
lr = theano.shared(np.float32(0.01)) # http://deeplearning.net/software/theano/library/compile/shared.html
best_loss = 100
best_loss_count = 0

best_params = lasagne.layers.get_all_param_values(network) # http://lasagne.readthedocs.org/en/latest/modules/layers/helper.html#lasagne.layers.get_all_param_values

prediction = lasagne.layers.get_output(network, deterministic=False) # http://lasagne.readthedocs.org/en/latest/modules/layers/helper.html#lasagne.layers.get_output
loss = lasagne.objectives.categorical_crossentropy(prediction, target_var) # http://lasagne.readthedocs.org/en/latest/modules/objectives.html#lasagne.objectives.categorical_crossentropy
loss = loss.mean()
params = lasagne.layers.get_all_params(network, trainable=True)
updates = lasagne.updates.nesterov_momentum(loss, params, learning_rate=lr, momentum=0.9) # http://lasagne.readthedocs.org/en/latest/modules/updates.html#lasagne.updates.nesterov_momentum

test_prediction = lasagne.layers.get_output(network, deterministic=True)
test_loss = lasagne.objectives.categorical_crossentropy(test_prediction, target_var)
test_loss = test_loss.mean()
test_acc = T.mean(T.eq(T.argmax(test_prediction, axis=1), target_var), dtype=theano.config.floatX) # http://deeplearning.net/software/theano/tutorial/modes.html

train_fun = theano.function([input_var, target_var], loss, updates=updates) # http://deeplearning.net/software/theano/library/compile/function.html
valid_fun = theano.function([input_var, target_var], [test_loss, test_acc])


for epoch in range(num_epochs):
	for inputs, targets in iterate_minibatches(x_train, y_train, 8, shuffle=True):
		_ = train_fun(inputs, targets)
	
	valid_err = 0
	valid_acc = 0
	valid_batches = 0
	for inputs, targets in iterate_minibatches(x_valid, y_valid, 8, shuffle=False):
		err, acc = valid_fun(inputs, targets)
		valid_err += err
		valid_acc += acc
		valid_batches += 1
		
	valid_loss = valid_err / valid_batches
	valid_acc = valid_acc / valid_batches
			
	print "Epoch: ", epoch,
	print "\t\tvalid_loss: ", format(valid_loss, '.6f'), "\t\tvalid_acc: ", format(valid_acc, '.6f')

	if valid_loss < best_loss:
		print "New best loss.."
		best_loss = valid_loss
		best_params = lasagne.layers.get_all_param_values(network) # http://lasagne.readthedocs.org/en/latest/modules/layers/helper.html#lasagne.layers.get_all_param_values
		best_loss_count = 0
	else:
		best_loss_count += 1
		if (best_loss_count%5) == 0:
			print "Updating learning rate.."
			learning_rate /= 10
			lr.set_value(np.float32(learning_rate))
		if best_loss_count == 20:
			print "..Early Stopping.."
			break

lasagne.layers.set_all_param_values(network, best_params) # http://lasagne.readthedocs.org/en/latest/modules/layers/helper.html#lasagne.layers.set_all_param_values


valid_acc = 0
valid_batches = 0
for inputs, targets in iterate_minibatches(x_valid, y_valid, 8, shuffle=False):
	err, acc = valid_fun(inputs, targets)
	valid_acc += acc
	valid_batches += 1
valid_acc = valid_acc / valid_batches

test_acc = 0
test_batches = 0
for inputs, targets in iterate_minibatches(x_test, y_test, 8, shuffle=False):
	err, acc = valid_fun(inputs, targets)
	test_acc += acc
	test_batches += 1
test_acc = test_acc/test_batches

print "\n\t\ttest_acc: ", format(test_acc, '.6f')

text_file.write("cnn_valid\t%s\tcnn_test\t%s" % (str(format(valid_acc, '.6f')), str(format(test_acc, '.6f'))))
text_file.write("\n")


with open('model.pickle', 'wb') as f:
    pickle.dump(network, f, -1) # https://docs.python.org/2/library/pickle.html


text_file.close()
T_time = (round(time()-totalTime, 3))/60
print "Total Time: ", T_time, "Min" "\n"



