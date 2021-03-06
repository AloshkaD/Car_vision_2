import os.path
import tensorflow as tf
import helper
import warnings
from distutils.version import LooseVersion
import project_tests as tests
data_prefix = '/home/a/SDC/Term3/CarND-Semantic-Segmentation/data/data_road/'
training_data_prefix = data_prefix + 'training/'
testing_data_prefix = data_prefix + 'testing/' 
vgg_path = '/home/a/SDC/Term3/CarND-Semantic-Segmentation/weights'
trained_models_path = '/home/a/SDC/Term3/CarND-Semantic-Segmentation/trained_model'
trained_models_filename = (trained_models_path +
                        'weights.{epoch:03d}-{val_loss:.3f}.hdf5')

# Check TensorFlow Version
assert LooseVersion(tf.__version__) >= LooseVersion('1.0'), 'Please use TensorFlow version 1.0 or newer.  You are using {}'.format(tf.__version__)
print('TensorFlow Version: {}'.format(tf.__version__))

# Check for a GPU
if not tf.test.gpu_device_name():
    warnings.warn('No GPU found. Please use a GPU to train your neural network.')
else:
    print('Default GPU Device: {}'.format(tf.test.gpu_device_name()))

    



def load_vgg(sess, vgg_path):
    """
    Load Pretrained VGG Model into TensorFlow.
    :param sess: TensorFlow Session
    :param vgg_path: Path to vgg folder, containing "variables/" and "saved_model.pb"
    :return: Tuple of Tensors from VGG model (image_input, keep_prob, layer3_out, layer4_out, layer7_out)
    """
    # TODO: Implement function
    #   Use tf.saved_model.loader.load to load the model and weights
     
   
    vgg_tag = 'vgg16'
    vgg_input_tensor_name = 'image_input:0'
    vgg_keep_prob_tensor_name = 'keep_prob:0'
    vgg_layer3_out_tensor_name = 'layer3_out:0'
    vgg_layer4_out_tensor_name = 'layer4_out:0'
    vgg_layer7_out_tensor_name = 'layer7_out:0'
    tf.saved_model.loader.load(sess, [vgg_tag], vgg_path)
    vgg_graph =  tf.get_default_graph()
    image_input = vgg_graph.get_tensor_by_name(vgg_input_tensor_name)
    keep_prob = vgg_graph.get_tensor_by_name(vgg_keep_prob_tensor_name)
    layer3_out = vgg_graph.get_tensor_by_name(vgg_layer3_out_tensor_name)
    layer4_out = vgg_graph.get_tensor_by_name(vgg_layer4_out_tensor_name)
    layer7_out = vgg_graph.get_tensor_by_name(vgg_layer7_out_tensor_name)
    return image_input, keep_prob, layer3_out, layer4_out, layer7_out 
tests.test_load_vgg(load_vgg, tf)


def layers(vgg_layer3_out, vgg_layer4_out, vgg_layer7_out, num_classes):
    """
    Create the layers for a fully convolutional network.  
    Build skip-layers using the vgg layers.
    :param vgg_layer7_out: TF Tensor for VGG Layer 3 output
    :param vgg_layer4_out: TF Tensor for VGG Layer 4 output
    :param vgg_layer3_out: TF Tensor for VGG Layer 7 output
    :param num_classes: Number of classes to classify
    :return: The Tensor for the last layer of output
    """
    # TODO: Implement function
    layer7_encoded = tf.layers.conv2d(vgg_layer7_out, num_classes, 1, 1)
    layer7_decoded = tf.layers.conv2d_transpose(layer7_encoded, num_classes, 4, 2, 'SAME')

    layer4_encoded = tf.layers.conv2d(vgg_layer4_out, num_classes, 1, 1)
    layer4_skipped = tf.add(layer7_decoded, layer4_encoded)
    layer4_decoded = tf.layers.conv2d_transpose(layer4_skipped, num_classes, 8, 2, 'SAME')

    layer3_encoded = tf.layers.conv2d(vgg_layer3_out, num_classes, 1, 1)
    layer3_skipped = tf.add(layer4_decoded, layer3_encoded)
    layer3_decoded = tf.layers.conv2d_transpose(layer3_skipped, num_classes, 16, 8, 'SAME')
    
    return layer3_decoded

tests.test_layers(layers)


def optimize(nn_last_layer, correct_label, learning_rate, num_classes):
    """
    Build the TensorFLow loss and optimizer operations.
    :param nn_last_layer: TF Tensor of the last layer in the neural network
    :param correct_label: TF Placeholder for the correct label image
    :param learning_rate: TF Placeholder for the learning rate
    :param num_classes: Number of classes to classify
    :return: Tuple of (logits, train_op, cross_entropy_loss)
    """
    
    # TODO: Implement function
    #Let's get some help in understanding reshape https://www.tensorflow.org/api_docs/python/tf/reshape
    """
    #reshape(t, [-1]) ==> [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 6, 6, 6]
    # -1 is inferred to be 2:
    
    reshape(t, [-1, 9]) ==> [[1, 1, 1, 2, 2, 2, 3, 3, 3],
                            [4, 4, 4, 5, 5, 5, 6, 6, 6]]
    """
    logits = tf.reshape(nn_last_layer, (-1, num_classes))
    labels = tf.reshape(correct_label, (-1, num_classes))
    cross_entropy_loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=labels))
    #return the tuples
    train_op = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cross_entropy_loss)
    return logits, train_op, cross_entropy_loss
tests.test_optimize(optimize)


def train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, 
             input_image,correct_label, keep_prob, learning_rate):
    """
    Train neural network and print out the loss during training.
    :param sess: TF Session
    :param epochs: Number of epochs
    :param batch_size: Batch size
    :param get_batches_fn: Function to get batches of training data.  Call using get_batches_fn(batch_size)
    :param train_op: TF Operation to train the neural network
    :param cross_entropy_loss: TF Tensor for the amount of loss
    :param input_image: TF Placeholder for input images
    :param correct_label: TF Placeholder for label images
    :param keep_prob: TF Placeholder for dropout keep probability
    :param learning_rate: TF Placeholder for learning rate
    """
    # TODO: Implement function
    #...create a graph...#
    # Launch the graph in a session.
    """
    #add embeddings 
    from tensorflow.contrib.tensorboard.plugins import projector

    # Create randomly initialized embedding weights which will be trained.
    N = 10000 # Number of items (vocab size).
    D = 200 # Dimensionality of the embedding.
    embedding_var = tf.Variable(tf.random_normal([N,D]), name='word_embedding')

    # Format: tensorflow/tensorboard/plugins/projector/projector_config.proto
    config = projector.ProjectorConfig()

    # You can add multiple embeddings. Here we add only one.
    embedding = config.embeddings.add()
    embedding.tensor_name = embedding_var.name
    # Link this tensor to its metadata file (e.g. labels).
    embedding.metadata_path = os.path.join(LOG_DIR, 'metadata.tsv')

    # Use the same LOG_DIR where you stored your checkpoint.
    summary_writer = tf.summary.FileWriter(LOG_DIR)

    # The next line writes a projector_config.pbtxt in the LOG_DIR. TensorBoard will
    # read this file during startup.
    projector.visualize_embeddings(summary_writer, config)
    """
    
    
    # Create a summary writer, add the 'graph' to the event file.
    log_dir='./logs'
    train_writer = tf.summary.FileWriter(log_dir+ '/train', sess.graph)
    test_writer = tf.summary.FileWriter(log_dir+ '/test')
    #tf.summary.image('input', input_image,batch_size)
    #tf.global_variables_initializer().run()
    #tf.local_variables_initializer().run()
    sess.run(tf.global_variables_initializer())
    print("Start Training...") 
    
    for i in range(epochs):
        iter_num = 0
        for images, labels in get_batches_fn(batch_size):
            iter_num = iter_num + 1
            if images.shape[0] != batch_size:
                continue
            _, loss= sess.run([train_op, cross_entropy_loss],
                feed_dict={input_image: images, correct_label: labels, keep_prob: 1.0, learning_rate:1e-3})
            print("Epoch {}/{}, Loss {:.5f}".format(i, iter_num, loss))
    #pass
tests.test_train_nn(train_nn)

 
def run():
    global g_iou
    global g_iou_op
    num_classes = 2
    image_shape = (160, 576)
    data_dir = './data'
    #data_dir = training_data_prefix
    runs_dir = './runs'
    tests.test_for_kitti_dataset(data_dir)
    epochs = 3
    batch_size = 1
    correct_label = tf.placeholder(tf.float32, shape=[batch_size, image_shape[0],image_shape[1], 2])
    learning_rate = tf.placeholder(tf.float32, shape=[])
    # Download pretrained vgg model
    helper.maybe_download_pretrained_vgg(data_dir)

    # OPTIONAL: Train and Inference on the cityscapes dataset instead of the Kitti dataset.
    # You'll need a GPU with at least 10 teraFLOPS to train on.
    #  https://www.cityscapes-dataset.com/

    with tf.Session() as sess:
        # Path to vgg model
        vgg_path = os.path.join(data_dir, 'vgg')
        # Create function to get batches
        get_batches_fn = helper.gen_batch_function(os.path.join(data_dir, 'data_road/training'), image_shape)

        # OPTIONAL: Augment Images for better results
        #  https://datascience.stackexchange.com/questions/5224/how-to-prepare-augment-images-for-neural-network

        # TODO: Build NN using load_vgg, layers, and optimize function
        input_image, keep_prob, vgg_layer3_out, vgg_layer4_out, vgg_layer7_out = load_vgg(sess, vgg_path)
        nn_last_layer = layers(vgg_layer3_out, vgg_layer4_out, vgg_layer7_out, num_classes)
        logits, train_op, cross_entropy_loss = optimize(nn_last_layer, correct_label, learning_rate, num_classes)
        g_iou, g_iou_op = tf.metrics.mean_iou(tf.argmax(tf.reshape(correct_label, (-1,2)), -1), tf.argmax(logits, -1), num_classes)
        # TODO: Train NN using the train_nn function
        train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, 
             input_image,correct_label, keep_prob, learning_rate)
        
        saver = tf.train.Saver()
        saver.save(sess, "./trained_model/model.ckpt")
        saver.export_meta_graph("./trained_model/model.meta")
        tf.train.write_graph(sess.graph_def, "./trained_model/", "model.pb", False)
        # TODO: Save inference data using helper.save_inference_samples
        
        helper.save_inference_samples(runs_dir, data_dir, sess, image_shape, logits, keep_prob, input_image)

        # OPTIONAL: Apply the trained model to a video


if __name__ == '__main__':
    run()
