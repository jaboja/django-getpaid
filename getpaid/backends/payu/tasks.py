import logging
from celery.task.base import task
from django.db.models.loading import get_model


logger = logging.getLogger('getpaid.backends.payu')


def _get_processor(payment_id, session_id):
    try:
        Payment = get_model('getpaid', 'Payment')
        payment_id = int(payment_id)
        try:
            payment = Payment.objects.get(pk=payment_id)
        except Payment.DoesNotExist:
            logger.error('Payment does not exist pk=%d' % payment_id)
            return None
        # Avoiding circular import
        from getpaid.backends.payu import PaymentProcessor
        processor = PaymentProcessor(payment)
    except Exception, ex:
        logger.error(
            'Task unable to get processor for payment (%d, %r): %r' % (
                payment_id, session_id, ex))
        raise
    else:
        logger.info("Got payment processor for payment (%d, %r)" % (
            payment_id, session_id))
        return processor


@task(max_retries=50, default_retry_delay=2 * 60)
def get_payment_status_task(payment_id, session_id):
    logger.info(
        "get_payment_status_task(%r, %r)..." % (payment_id, session_id))
    processor = _get_processor(payment_id, session_id)
    if processor is not None:
        processor.get_payment_status(session_id)
        logger.info(
            "get_payment_status_task(%r, %r) OK" % (payment_id, session_id))


@task(max_retries=50, default_retry_delay=2 * 60)
def accept_payment(payment_id, session_id):
    logger.info(
        "accept_payment(%r, %r)..." % (payment_id, session_id))
    processor = _get_processor(payment_id, session_id)
    if processor is not None:
        processor.accept_payment(session_id)
        logger.info(
            "accept_payment(%r, %r) OK" % (payment_id, session_id))
